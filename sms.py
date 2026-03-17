import os
from twilio.rest import Client


def send_agent_text(agent_phone, buyer_name, score, tier, probability, max_price, report_url):
    account_sid = os.environ["TWILIO_ACCOUNT_SID"]
    auth_token = os.environ["TWILIO_AUTH_TOKEN"]
    from_phone = os.environ["TWILIO_FROM_PHONE"]

    client = Client(account_sid, auth_token)

    body = (
        f"New Lead Scoring AI submission\n"
        f"Buyer: {buyer_name}\n"
        f"Score: {score}\n"
        f"Tier: {tier}\n"
        f"Close Probability: {round(probability * 100)}%\n"
        f"Max Price: ${round(max_price):,}\n"
        f"Report: {report_url}"
    )

    message = client.messages.create(
        body=body,
        from_=from_phone,
        to=agent_phone
    )

    return message.sid