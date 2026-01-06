# database_setup.py
from app.services.postgres_service import postgres_service

def create_tables_if_not_exist():
    """ایجاد جداول در صورت عدم وجود"""
    
    # 1. ایجاد extension pgcrypto
    create_extension_sql = "CREATE EXTENSION IF NOT EXISTS pgcrypto;"
    
    # 2. ایجاد جدول properties
    create_table_sql = """
        CREATE TABLE IF NOT EXISTS public.properties (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID,
            title VARCHAR(255),
            description TEXT,
            property_type VARCHAR(50),
            transaction_type VARCHAR(50),
            status VARCHAR(50) DEFAULT 'تایید_شده',
            price INTEGER DEFAULT 0,
            area INTEGER DEFAULT 0,
            city VARCHAR(100),
            district VARCHAR(100),
            owner_phone VARCHAR(20),
            bedrooms INTEGER,
            age INTEGER,
            year_built INTEGER,
            floor INTEGER,
            total_floors INTEGER,
            document_type VARCHAR(50),
            has_parking BOOLEAN DEFAULT FALSE,
            has_elevator BOOLEAN DEFAULT FALSE,
            has_storage BOOLEAN DEFAULT FALSE,
            is_renovated BOOLEAN DEFAULT FALSE,
            open_to_exchange BOOLEAN DEFAULT FALSE,
            exchange_preferences JSONB DEFAULT '{}'::jsonb,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """
    
    # 3. ایجاد تابع برای updated_at
    create_function_sql = """
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """
    
    # 4. ایجاد trigger
    create_trigger_sql = """
        DROP TRIGGER IF EXISTS update_properties_updated_at ON public.properties;
        CREATE TRIGGER update_properties_updated_at
        BEFORE UPDATE ON public.properties
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    """
    
    try:
        print("ایجاد extension pgcrypto...")
        postgres_service.execute_raw(create_extension_sql)
        
        print("ایجاد جدول properties...")
        postgres_service.execute_raw(create_table_sql)
        
        print("ایجاد تابع update_updated_at_column...")
        postgres_service.execute_raw(create_function_sql)
        
        print("ایجاد trigger...")
        postgres_service.execute_raw(create_trigger_sql)
        
        print("✅ تمام جداول با موفقیت ایجاد شدند.")
        return True
        
    except Exception as e:
        print(f"❌ خطا در ایجاد جداول: {e}")
        return False