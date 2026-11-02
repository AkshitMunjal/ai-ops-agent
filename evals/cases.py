cases = [
    {
        "name": "plain order",
        "email": """Hi,

This is Gupta Stores. Please send us 40 steel bolts M8 and
3 rolls of copper wire 2.5mm by next week.

Thanks,
Rakesh""",
        "expected_customer": "Gupta Stores",
        "expected_lines": [("steel bolts M8", 40), ("copper wire 2.5mm", 3)],
    },
    {
        "name": "shop name only in the signature",
        "email": """Hello,

Please send 5 steel bolts M8 this week.

Regards,
Rakesh Gupta
Gupta Stores""",
        "expected_customer": "Gupta Stores",
        "expected_lines": [("steel bolts M8", 5)],
    },
    {
        "name": "only a person name",
        "email": """Hello, this is Sunil. Please send 10 copper wire 2.5mm.""",
        "expected_customer": "Sunil",
        "expected_lines": [("copper wire 2.5mm", 10)],
    },
    {
        "name": "quantities written in words",
        "email": """Gupta Stores here. Please send two rolls of copper wire 2.5mm
and ten steel bolts M8.""",
        "expected_customer": "Gupta Stores",
        "expected_lines": [("copper wire 2.5mm", 2), ("steel bolts M8", 10)],
    },
    {
        "name": "a dozen",
        "email": """Gupta Stores: please send a dozen steel bolts M8.""",
        "expected_customer": "Gupta Stores",
        "expected_lines": [("steel bolts M8", 12)],
    },
    {
        "name": "bullet list with x quantities",
        "email": """Order from Gupta Stores:

- steel bolts M8 x 25
- copper wire 2.5mm x 4

Please confirm.""",
        "expected_customer": "Gupta Stores",
        "expected_lines": [("steel bolts M8", 25), ("copper wire 2.5mm", 4)],
    },
    {
        "name": "po number and date are not products",
        "email": """Gupta Stores, PO number 1042, dated 28 October 2026.
Please send 25 steel bolts M8 by 6 November.""",
        "expected_customer": "Gupta Stores",
        "expected_lines": [("steel bolts M8", 25)],
    },
    {
        "name": "text of the real PDF email",
        "email": """From: Rakesh Gupta <gupta@example.com>
Subject: Purchase order PO-1042

Hello,

Please find our purchase order attached.

Regards,
Rakesh

Attachment PO-1042.pdf:
Purchase Order
PO number PO-1042 | Date 28 October 2026
ORDERED BY
Gupta Stores
Model Town, Ludhiana
gupta@example.com
DELIVER BY
Friday, 6 November 2026
ITEM DESCRIPTION QUANTITY
1 Steel Bolts M8 25
2 Copper Wire 2.5mm 4
Please confirm availability and send the invoice with the delivery.
Regards,
Rakesh Gupta
Gupta Stores""",
        "expected_customer": "Gupta Stores",
        "expected_lines": [("steel bolts M8", 25), ("copper wire 2.5mm", 4)],
    },
]