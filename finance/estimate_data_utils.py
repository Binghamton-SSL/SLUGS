import decimal
from django.utils import timezone


def calculateGigCost(estimate):
    ret = {
        "no_loadins": False,
        "systems": {},
        "subcontracted_equipment": {},
        "fees": {},
        "subtotal": decimal.Decimal(0.00),
        "subcontracted_amount": decimal.Decimal(0.00),
        "fees_amt": decimal.Decimal(0.00),
        "payment_amt": decimal.Decimal(0.00),
        "total_amt": decimal.Decimal(0.00),
        "outstanding_balance": decimal.Decimal(0.00),
    }
    ret["estimate"] = estimate
    ret["gig"] = ret["estimate"].gig
    ret["loadins"] = ret["gig"].loadin_set.order_by("shop_time")
    if (ret["loadins"].count() < 1):
        ret["no_loadins"] = True
    if not ret["no_loadins"]:
        # Format first/last loadin times for use on printed documents
        ret["first_shop_time"] = ret["loadins"].first().shop_time
        ret["first_load_in"] = ret["loadins"].first().load_in
        ret["last_load_out"] = ret["gig"].loadin_set.order_by("-load_out").first().load_out
        # Format All system / addon costs
        for systeminstance in (
            ret["gig"].systeminstance_set.all().order_by("system__department")
        ):
            system = systeminstance.system
            dept = system.department
            dept_loadins = ret["loadins"].filter(department=dept)

            current_price = system.get_price_at_date(ret["gig"].start)

            system_subtotal = decimal.Decimal(0.00)

            rented_start = dept_loadins.order_by("shop_time").first().shop_time
            rented_end = dept_loadins.order_by("-load_out").first().load_out
            total_time_rented = decimal.Decimal(
                (rented_end - rented_start) / timezone.timedelta(minutes=15) / 4
            )

            total_loadin_time = decimal.Decimal(0.00)
            total_show_time = decimal.Decimal((ret["gig"].end - ret["gig"].setup_by) / timezone.timedelta(minutes=15) / 4)
            for loadin in dept_loadins.order_by("shop_time"):
                total_loadin_time += decimal.Decimal(
                    (
                        # Add total time for this loadin, accounts for load ins that occur entirely before or after concert
                        (
                            (ret["gig"].setup_by - loadin.shop_time)
                            if ret["gig"].setup_by < loadin.load_out
                            and ret["gig"].start > loadin.shop_time
                            else (loadin.load_out - loadin.shop_time)
                        )  # noqa Add shop time to gig start if gig start is before load out, otherwise go from shop time to load out
                        + (
                            # Ignore loadin that starts during show and ends after show (handled above), if not, check if load out is before gig starts else add 0
                            timezone.timedelta(minutes=0)
                            if loadin.shop_time > ret["gig"].start
                            else (loadin.load_out - ret["gig"].end)
                            if loadin.load_out > ret["gig"].end
                            else timezone.timedelta(minutes=0)
                        )
                    )
                    / timezone.timedelta(minutes=15)
                    / 4
                )

            system_subtotal += round(
                current_price.base_price + current_price.price_per_hour * total_time_rented,
                2,
            )

            ret["systems"][systeminstance] = [
                system,
                total_time_rented if current_price.price_per_hour else 1,
                system_subtotal,
                False,
            ]
            addons = systeminstance.addoninstance_set.all()
            for addon_set_item in addons:
                addon = addon_set_item.addon
                addon.description = f"{(f'{addon.description}') if addon.description else ''} {f' - {addon_set_item.description}' if addon_set_item.description else ''}"

                current_price = addon.get_price_at_date(ret["gig"].start)

                addon_subtotal = round(
                    current_price.base_price * addon_set_item.qty
                    + (
                        current_price.price_per_hour
                        * addon_set_item.qty
                        * total_time_rented
                    )
                    + (
                        current_price.price_per_hour_for_load_in_out_ONLY
                        * addon_set_item.qty
                        * total_loadin_time
                    )
                    + (
                        current_price.price_per_hour_for_show_ONLY
                        * addon_set_item.qty
                        * total_show_time
                    ),
                    2,
                )
                system_subtotal += addon_subtotal

                ret["systems"][addon_set_item.pk] = [
                    addon,
                    addon_set_item.qty * total_time_rented
                    if current_price.price_per_hour != 0.00
                    else addon_set_item.qty * total_loadin_time
                    if current_price.price_per_hour_for_load_in_out_ONLY != 0.00
                    else addon_set_item.qty * total_show_time
                    if current_price.price_per_hour_for_show_ONLY != 0.00
                    else addon_set_item.qty,
                    addon_subtotal,
                    True,
                ]
            ret["subtotal"] += system_subtotal
            ret["total_amt"] += system_subtotal

    for rental in ret["estimate"].gig.subcontractedequipment_set.all():
        ret["subcontracted_equipment"][rental.pk] = {
            "vendor": rental.vendor,
            "vendor_visible_to_client": rental.vendor_visible_to_client,
            "client_provided": rental.client_provided,
            "fees": [],
            "equipment": {},
        }
        vendor_subtotal = decimal.Decimal(0.00)
        for instance in rental.subcontractedequipmentinstance_set.all():
            if rental.client_provided:
                ret["subcontracted_equipment"][rental.pk]["equipment"][instance.pk] = [
                    instance,
                    instance.qty * total_time_rented
                    if current_price.price_per_hour != 0.00
                    else instance.qty,
                    0,
                    0
                ]
            else:
                subtotal = decimal.Decimal(0.00)
                total_time_rented = decimal.Decimal(
                    (rental.returned - rental.arrival) / timezone.timedelta(minutes=15) / 4
                )
                current_price = instance.equipment.get_price_at_date(rental.arrival)
                subtotal += round(
                    current_price.base_price * instance.qty
                    + (
                        current_price.price_per_hour
                        * instance.qty
                        * total_time_rented
                    ), 2
                )
                vendor_subtotal += subtotal
                ret["subcontracted_equipment"][rental.pk]["equipment"][instance.pk] = [
                    instance,
                    instance.qty * total_time_rented
                    if current_price.price_per_hour != 0.00
                    else instance.qty,
                    current_price.price_per_hour if current_price.price_per_hour != 0.00 else current_price.base_price,
                    subtotal
                ]
        for fee in rental.vendorfee_set.all():
            amount = round(fee.percentage*subtotal+fee.amount, 2);
            ret["subcontracted_equipment"][rental.pk]["fees"].append([fee, amount])
            vendor_subtotal += amount

        ret["subcontracted_amount"] += vendor_subtotal
        ret["total_amt"] += vendor_subtotal

    for fee in ret["estimate"].onetimefee_set.order_by("order").all():
        fee_amt = (
            fee.amount
            if fee.amount
            else round(ret["total_amt"] * (fee.percentage / 100), 2)
        )
        ret["fees"][fee] = [fee, fee_amt]
        ret["fees_amt"] += fee_amt
        ret["total_amt"] += fee_amt

    for payment in ret["estimate"].payment_set.all():
        ret["payment_amt"] += payment.amount

    ret["total_amt"] = ret["total_amt"] + ret["estimate"].adjustments
    ret["outstanding_balance"] = ret["total_amt"] - ret["payment_amt"]
    return ret


def calcuateSubcontractedCost(subcontracted):
    ret = {
        "subcontracted": subcontracted,
        "subtotal": decimal.Decimal(0.00),
        "total_amt": decimal.Decimal(0.00),
        "fee_amt": decimal.Decimal(0.00),
        "fees": [],
        "equipment": {},
    }
    for instance in subcontracted.subcontractedequipmentinstance_set.all():
        subtotal = decimal.Decimal(0.00)
        total_time_rented = decimal.Decimal(
            (subcontracted.returned - subcontracted.arrival) / timezone.timedelta(minutes=15) / 4
        )
        current_price = instance.equipment.get_price_at_date(subcontracted.arrival)
        subtotal += round(
            current_price.base_price * instance.qty
            + (
                current_price.price_per_hour
                * instance.qty
                * total_time_rented
            ), 2
        )
        ret["total_amt"] += subtotal
        ret["equipment"][instance] = [
            instance,
            instance.qty * total_time_rented
            if current_price.price_per_hour != 0.00
            else instance.qty,
            current_price.price_per_hour if current_price.price_per_hour != 0.00 else current_price.base_price,
            subtotal
        ]
        ret["subtotal"] += subtotal
    for fee in subcontracted.vendorfee_set.all():
        amount = round(fee.percentage*subtotal+fee.amount, 2);
        ret["fees"].append([fee, amount])
        ret["fee_amt"] += amount
    ret["total_amt"] += ret["fee_amt"]
    return ret
