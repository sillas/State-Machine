def lambda_handler(event, context):

    print("LAMBDA", __name__)

    print(f"Saimos do centro! {event["value"]}")
    return None