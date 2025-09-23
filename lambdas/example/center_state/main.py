from time import sleep


def lambda_handler(event, context):

    print("LAMBDA", __name__)
    print(f"Estamos no centro! {event["value"]}")

    sleep(5)

    event["value"] += 1
    return event
