import decimal

from django.utils import timezone


def calculateGigCost(estimate):
    ret = {
        "systems": {},
        "fees": {},
        "subtotal": decimal.Decimal(0.00),
        "fees_amt": decimal.Decimal(0.00),
        "payment_amt": decimal.Decimal(0.00),
        "total_amt": decimal.Decimal(0.00),
        "outstanding_balance": decimal.Decimal(0.00),
    }
    ret["estimate"] = estimate
    ret["gig"] = ret["estimate"].gig
    ret["loadins"] = ret["gig"].loadin_set.order_by("shop_time")
    # Format first/last loadin times for use on printed documents
    ret["first_shop_time"] = ret["loadins"].first().shop_time
    ret["first_load_in"] = ret["loadins"].first().load_in
    ret["last_load_out"] = ret["loadins"].first().load_out
    # Format All system / addon costs
    for system in ret["gig"].systems.all().order_by("department"):
        dept = system.department
        dept_loadins = ret["loadins"].filter(department=dept)

        system_subtotal = decimal.Decimal(0.00)

        rented_start = dept_loadins.order_by("shop_time").first().shop_time
        rented_end = dept_loadins.order_by("-load_out").first().load_out
        total_time_rented = decimal.Decimal(
            (rented_end - rented_start) / timezone.timedelta(minutes=15) / 4
        )

        total_loadin_time = decimal.Decimal(0.00)
        for loadin in dept_loadins.order_by("shop_time"):
            total_loadin_time += decimal.Decimal(
                (
                    # Add total time for this loadin, accounts for load ins that occur entirely before or after concert
                    (
                        (ret["gig"].setup_by - loadin.shop_time)
                        if ret["gig"].setup_by < loadin.load_out
                        and ret["gig"].end > loadin.shop_time
                        else (
                            loadin.load_out - loadin.shop_time
                        )
                    )  # noqa Add shop time to gig start if gig start is before load out, otherwise go from shop time to load out
                    + (
                        (loadin.load_out - ret["gig"].end)
                        if loadin.load_out
                        > ret["gig"].end  # noqa Add show end to load out if load out is after end of gig, otherwise add nothing
                        else 0
                    )
                )
                / timezone.timedelta(minutes=15) / 4
            )

        system_subtotal += round(
            system.base_price + system.price_per_hour * total_time_rented,
            2,
        )

        ret["systems"][system] = [
            system,
            total_time_rented if system.price_per_hour else 1,
            system_subtotal,
            False,
        ]
        addons = system.systeminstance_set.get(gig_id=ret["gig"].pk).addoninstance_set.all()
        for addon_set_item in addons:
            addon = addon_set_item.addon
            addon.addl_description = addon_set_item.description

            addon_subtotal = round(
                addon.base_price * addon_set_item.qty
                + (
                    addon.price_per_hour_for_duration_of_gig
                    * addon_set_item.qty
                    * total_time_rented
                )
                + (
                    addon.price_per_hour_for_load_in_out_ONLY
                    * addon_set_item.qty
                    * total_loadin_time
                ),
                2,
            )
            system_subtotal += addon_subtotal

            ret["systems"][addon_set_item.pk] = [
                addon,
                addon_set_item.qty * total_time_rented
                if addon.price_per_hour_for_duration_of_gig != 0.00
                else addon_set_item.qty * total_loadin_time
                if addon.price_per_hour_for_load_in_out_ONLY
                else addon_set_item.qty,
                addon_subtotal,
                True,
            ]
        ret["subtotal"] += system_subtotal

    for fee in ret["estimate"].fees.all():
        fee_amt = (
            fee.amount
            if fee.amount
            else round(ret["estimate"].subtotal * (fee.percentage / 100), 2)
        )
        ret["fees"][fee] = [fee, fee_amt]
        ret["fees_amt"] += fee_amt

    for fee in ret["estimate"].onetimefee_set.all():
        fee_amt = (
            fee.amount
            if fee.amount
            else round(ret["estimate"].subtotal * (fee.percentage / 100), 2)
        )
        ret["fees"][fee] = [fee, fee_amt]
        ret["fees_amt"] += fee_amt

    for payment in ret["estimate"].payment_set.all():
        ret["payment_amt"] += payment.amount

    ret["total_amt"] = ret["subtotal"] + ret["fees_amt"] + ret["estimate"].adjustments
    ret["outstanding_balance"] = ret["total_amt"] - ret["payment_amt"]
    return ret
