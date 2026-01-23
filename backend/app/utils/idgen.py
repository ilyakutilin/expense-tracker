import random
import string
import time


def generate_request_id():
    timestamp = str(int(time.time()))[-7:]
    random_part = "".join(random.choices(string.ascii_letters + string.digits, k=5))
    return f"{timestamp}{random_part}"


if __name__ == "__main__":
    print(generate_request_id())
