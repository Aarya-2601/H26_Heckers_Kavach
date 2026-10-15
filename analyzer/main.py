# We used to call requests directly here, now we go through api_client
from src.api_client import fetch_user_data


def main():
    print("requests are handled in api_client")
    print(fetch_user_data(1))


if __name__ == "__main__":
    main()
