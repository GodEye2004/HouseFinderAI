from app.core.postgres_service import postgres_service

if __name__ == "__main__":
    try:
        if postgres_service.test_connection():
            print("Database connection successful")
        else:
            print("Database responded, but something is wrong")
    except Exception as e:
        print("Database connection failed")
        print(e)
