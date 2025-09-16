from time import sleep


def lambda_handler(event, context):

    print("LAMBDA", __name__)
    print(f"Saimos do centro! {event["value"]}")

    sleep(4)

    return event["value"]
