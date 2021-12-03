from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from utils.models import signupStatus, onboardingStatus

from finance.models import Wage
from equipment.models import System, SystemAddon
from finance.models import Fee


class Command(BaseCommand):
    help = "Sets up environment for development (create Manager group, ...)"

    def handle(self, *args, **options):
        # Create signup status
        signupStatus.objects.get_or_create(is_open=False)
        # Create onboarding status
        onboardingStatus.objects.get_or_create(is_open=False)
        # Create deafult wages and groups
        WAGES = [
            ("Tech", 11.80),
            ("Engineer", 11.90),
            ("Senior Engineer", 12.00),
            ("Manager", 12.20),
            ("GM & FD", 13.00),
            ("Stage", 15.00),
        ]
        for wage_name, rate in WAGES:
            Wage.objects.get_or_create(name=wage_name, hourly_rate=rate)
        GROUPS = [
            ("Bi-Amping Engineer", "Engineer"),
            ("Conditional Hire", "Tech"),
            ("Junior Engineer", "Engineer"),
            ("Large Engineer", "Senior Engineer"),
            ("Lighting", "Tech"),
            ("Lighting Load in / out", "Tech"),
            ("Lighting Tech", "Tech"),
            ("Medium Engineer", "Engineer"),
            ("New Hire", "Tech"),
            ("Probie - Lighting", "Tech"),
            ("Probie - Sound", "Tech"),
            ("Senior Engineer", "Senior Engineer"),
            ("Small Engineer", "Engineer"),
            ("Sound", "Tech"),
            ("Sound Load in / out", "Tech"),
            ("Sound Tech", "Tech"),
            ("Manager", "Manager"),
            ("Financial Director/GM", "GM & FD"),
            ("Stagehand", "Stage"),
        ]
        for group_name, rate in GROUPS:
            wage = Wage.objects.get(name=rate)
            Group.objects.get_or_create(name=group_name, hourly_rate=wage)
        SYSTEMS = [
            ("Uplighting", "", "L", 50, 0),
            ("Alt-Uplighting", "", "L", 50, 0),
            ("Small", "", "L", 0, 13),
            ("Alt-Small", "", "L", 0, 13),
            ("Medium", "", "L", 0, 26),
            ("Alt-Medium", "", "L", 0, 26),
            ("Large", "", "L", 0, 26),
            ("D", "", "S", 0, 13),
            ("C", "", "S", 0, 13),
            ("B", "", "S", 0, 26),
            ("A", "", "S", 0, 26),
            ("AA", "", "S", 0, 26),
        ]
        SYSTEM_ADDONS = [
            (
                "Stage Labor",
                "T",
                "",
                0,
                13,
            ),  # <- This doesn't work because it's not hourly to the gig, it's a setup thing. # noqa
            (
                "Deluxe Live Act Package",
                "S",
                "Full band mics/equipment and up to up to 6 monitor mixes. Tech replaced by monitor engineer on laptop",  # noqa
                85,
                0,
            ),
            (
                "Live Act Package",
                "S",
                "Dancers/Singers/Musicians - Up to 2 monitors; Includes all cables, mics, equipment; Drum set OKAY if not mic'ed",  # noqa
                50,
                0,
            ),
            ("Acapella Hourly Rate", "S", "", 0, 13),
            ("Sr. Engineer Hourly", "O", "", 0, 13),
            ("Tech Hourly", "O", "", 0, 13),
            ("Engineer Hourly", "O", "", 0, 13),
            ("Labor Hourly", "O", "", 0, 13),
            (
                "Band Equipment",
                "S",
                "Full band mics/equipment and up to 6 monitor mixes",
                75,
                0,
            ),
            (
                "Performer Equipment",
                "S",
                "Live performance; Guitar, vocals, piano, cultural (No drumsets) - includes all necessary extra equipment (up to 3 monitors, mics, cables)",  # noqa
                50,
                0,
            ),
            (
                "Monitor World",
                "S",
                "Unlimited monitors, full band mics/equipment, includes monitor board and tech replaced by engineer",
                85,
                0,
            ),
            ("Monitor Wedge", "S", "", 20, 0),
            ("Wireless Handheld Mic", "S", "", 15, 0),
            ("Tent", "O", "Pop up tent", 20, 0),
            ("Backdrop", "L", "Available only with Large Lights", 20, 0),
            (
                "Backdrop with Truss",
                "L",
                "For non-Large Lighting Shows (Note - trussing may block the projector)",
                50,
                0,
            ),
            ("Spotlight", "L", "", 25, 0),
            ("Spotlight Operator", "L", "Hourly rate for spotlight operator", 0, 13),
            ("Blacklight", "L", "", 15, 0),
            ("Strobe Light", "L", "", 15, 0),
            ("Moving Head Lights", "L", "Four moving head lights", 80, 0),
        ]
        for sys_name, sys_desc, sys_dept, sys_price, sys_hourly in SYSTEMS:
            System.objects.get_or_create(
                name=sys_name,
                description=sys_desc,
                department=sys_dept,
                base_price=sys_price,
                price_per_hour=sys_hourly,
            )
        for sys_name, sys_dept, sys_desc, sys_price, sys_hourly in SYSTEM_ADDONS:
            SystemAddon.objects.get_or_create(
                name=sys_name,
                description=sys_desc,
                department=sys_dept,
                base_price=sys_price,
                price_per_hour_for_duration_of_gig=sys_hourly,
            )
        # PERMISSIONS_FOR_MANAGERS = [
        #     12,
        #     61,
        #     62,
        #     63,
        #     64,
        #     65,
        #     66,
        #     67,
        #     68,
        #     45,
        #     46,
        #     47,
        #     48,
        #     49,
        #     50,
        #     51,
        #     52,
        #     53,
        #     54,
        #     55,
        #     56,
        #     77,
        #     78,
        #     79,
        #     80,
        #     69,
        #     70,
        #     71,
        #     72,
        #     73,
        #     74,
        #     75,
        #     76,
        #     97,
        #     98,
        #     99,
        #     100,
        #     101,
        #     102,
        #     103,
        #     104,
        #     117,
        #     118,
        #     119,
        #     120,
        #     109,
        #     110,
        #     111,
        #     112,
        #     108,
        #     21,
        #     22,
        #     23,
        #     24,
        #     25,
        #     26,
        #     27,
        #     28,
        #     29,
        #     30,
        #     31,
        #     32,
        #     37,
        #     38,
        #     39,
        #     40,
        #     33,
        #     34,
        #     35,
        #     36,
        #     81,
        #     82,
        #     83,
        #     84,
        #     121,
        #     122,
        #     123,
        #     124,
        #     129,
        #     130,
        #     131,
        #     132,
        #     125,
        #     126,
        #     127,
        #     128,
        #     93,
        #     94,
        #     95,
        #     96,
        # ]
        # PERMISSIONS_FOR_FDGM = [
        #     97,
        #     98,
        #     99,
        #     100,
        #     101,
        #     102,
        #     103,
        #     104,
        #     117,
        #     118,
        #     119,
        #     120,
        #     113,
        #     114,
        #     115,
        #     116,
        #     109,
        #     110,
        #     111,
        #     112,
        #     105,
        #     106,
        #     107,
        #     108,
        # ]
        # manager_group = Group.objects.get(name="Manager")
        # manager_group.permissions.set(PERMISSIONS_FOR_MANAGERS)
        # manager_group = Group.objects.get(name="Financial Director/GM")
        # manager_group.permissions.set(PERMISSIONS_FOR_FDGM)
        FEES = [
            ("Booking Fee", "", 100, 0),
            ("UHaul Van", "", 70, 0),
            ("UHaul 14/17 ft Truck", "", 80, 0),
            ("UHaul 24/26 ft Truck", "", 100, 0),
            ("Extended Travel", "Milage + Gas", 80, 0),
            (
                "Cancelation Fee - Early",
                "Cancelling a system between one Monday and 48 hours prior will incur a 15% fee",
                0,
                15,
            ),  # noqa
            (
                "Cancelation Fee",
                "Between 24 and 48 hours prior to the event will incur a 50% fee",
                0,
                50,
            ),
            (
                "Cancelation Fee - Day of",
                "Any cancellations done the day of the event, or if the promoter neglects to inform BSSL of the event being cancelled, the group will be charge an additional 100% fee.",  # noqa
                0,
                100,
            ),  # noqa
            ("Late Booking Fee", "Booked less than 1 Monday prior to event", 0, 50),
            ("Late Nite Discount", "", -20, 0),
        ]
        for fee_name, fee_desc, fee_price, fee_percentage in FEES:
            Fee.objects.get_or_create(
                name=fee_name,
                description=fee_desc,
                amount=fee_price,
                percentage=fee_percentage,
            )


# Permission List
