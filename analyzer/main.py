try:
    from analyzer.api_client import fetch_user_data
except ImportError:
    from api_client import fetch_user_data


def main():
    print("requests are handled in api_client")
    print(fetch_user_data(1))


if __name__ == "__main__":
    main()
