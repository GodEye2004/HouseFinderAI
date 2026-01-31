import json
from typing import List, Dict, Optional, Any
from datetime import datetime
from app.models.property_submission import PropertySubmission, PropertySubmissionWithStatus, PropertyStatus
from app.models.property import Property, PropertyType, TransactionType, DocumentType
from app.core.postgres_service import postgres_service as database_service
import uuid

class PropertyManager:
    """ manage ads with PostgreSQL"""

    def __init__(self):
        pass

    def _map_status_to_db(self, status: str) -> str:
        if status == PropertyStatus.PENDING:
            return 'در_انتظار_تایید'
        elif status == PropertyStatus.APPROVED:
            return 'تایید_شده'
        elif status == PropertyStatus.REJECTED:
            return 'رد_شده'
        return 'در_انتظار_تایید'

    def _map_status_from_db(self, status: str) -> str:
        if status == 'در_انتظار_تایید':
            return PropertyStatus.PENDING
        elif status == 'تایید_شده':
            return PropertyStatus.APPROVED
        elif status == 'رد_شده':
            return PropertyStatus.REJECTED
        return PropertyStatus.PENDING

    def submit_property(
            self,
            submission: PropertySubmission,
            user_id: Optional[str] = None
    ) -> PropertySubmissionWithStatus:
        """ add new ads in PostgreSQL"""

        property_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        # calculate age of building
        age = None
        if submission.year_built:

            current_year = 1403  
            age = current_year - submission.year_built

        # ready data for save
        db_data = {
            "id": property_id,
            "user_id": user_id,
            "owner_phone": submission.owner_phone or "",
            "title": submission.title or "",
            "description": submission.description or "",
            "property_type": submission.property_type,
            "transaction_type": submission.transaction_type,
            "status": 'تایید_شده',  # approved defult.
            "price": submission.price or 0,
            "area": submission.area or 0,
            "city": submission.city or "",
            "district": submission.district or "",
            "bedrooms": submission.bedrooms,
            "age": age,
            "year_built": submission.year_built,
            "floor": submission.floor or 0,
            "total_floors": submission.total_floors or 0,
            "document_type": submission.document_type or "",
            "has_parking": submission.has_parking,
            "has_elevator": submission.has_elevator,
            "has_storage": submission.has_storage,
            "is_renovated": submission.is_renovated or False,
            "open_to_exchange": submission.open_to_exchange,
            "exchange_preferences": json.dumps(submission.exchange_preferences) if submission.exchange_preferences else json.dumps([]),
            "created_at": now,
            "updated_at": now
        }

        # delete None fields
        db_data = {k: v for k, v in db_data.items() if v is not None}

        # save in PostgreSQL
        try:
            result = database_service.insert("properties", db_data)
            if not result:
                raise Exception("error in create ads")
        except Exception as e:
            print(f"error in create ads :  {e}")
            raise

        # create return object
        return PropertySubmissionWithStatus(
            id=property_id,
            status=PropertyStatus.APPROVED,
            created_at=now,
            updated_at=now,
            **submission.dict()
        )

    def get_submission(self, property_id: str) -> Optional[PropertySubmissionWithStatus]:
        """get ads from PostgreSQL"""
        try:
            results = database_service.select("properties", filters={"id": property_id})
            if not results:
                return None
            
            data = results[0]
            return self._map_db_to_submission(data)
        except Exception as e:
            print(f"error to get ads :  {e}")
            return None

    def get_user_submissions(self, user_id: str) -> List[PropertySubmissionWithStatus]:
        """fetch ads from one user"""
        try:
            results = database_service.select("properties", filters={"user_id": user_id})
            return [self._map_db_to_submission(item) for item in results]
        except Exception as e:
            print(f" error to get user ads :  {e}")
            return []

    def get_all_submissions(
            self,
            status: Optional[PropertyStatus] = None,
            limit: int = 100,
            offset: int = 0
    ) -> List[PropertySubmissionWithStatus]:
        """get all ads """
        try:
            filters = {}
            if status:
                filters["status"] = self._map_status_to_db(status)
            
            results = database_service.select(
                "properties", 
                filters=filters,
                limit=limit,
                offset=offset
            )
            
            submissions = [self._map_db_to_submission(item) for item in results]
            submissions.sort(key=lambda x: x.created_at if x.created_at else "", reverse=True)
            return submissions
        except Exception as e:
            print(f" error to get all ads : {e}")
            return []

    def update_status(
            self,
            property_id: str,
            new_status: PropertyStatus,
            admin_note: Optional[str] = None
    ) -> bool:
        """change ads state"""
        db_status = self._map_status_to_db(new_status)
        try:
            update_data = {
                "status": db_status,
                "updated_at": datetime.now().isoformat()
            }
            if admin_note:
                update_data["admin_note"] = admin_note
                
            result = database_service.update("properties", property_id, update_data)
            return bool(result)
        except Exception as e:
            print(f"error in update ads state {e}")
            return False

    def delete_submission(self, property_id: str) -> bool:
        """delete ads"""
        try:
            return database_service.delete("properties", property_id)
        except Exception as e:
            print(f"error in delete ads :  {e}")
            return False

    def _map_db_to_submission(self, data: Dict) -> PropertySubmissionWithStatus:
        """change data in DB to pythom model"""
        created_at = data.get("created_at")
        updated_at = data.get("updated_at")
        
        if isinstance(created_at, datetime):
            created_at = created_at.isoformat()
        if isinstance(updated_at, datetime):
            updated_at = updated_at.isoformat()

        year_built = data.get("year_built")
        if year_built is None and data.get("age") is not None:
            year_built = 1403 - data.get("age")

        return PropertySubmissionWithStatus(
            id=data["id"],
            status=self._map_status_from_db(data.get("status", "در_انتظار_تایید")),
            created_at=created_at or "",
            updated_at=updated_at or "",
            owner_phone=data.get("owner_phone"),
            title=data.get("title"),
            description=data.get("description"),
            property_type=data.get("property_type"),
            transaction_type=data.get("transaction_type"),
            price=data.get("price"),
            area=data.get("area"),
            city=data.get("city"),
            district=data.get("district"),
            bedrooms=data.get("bedrooms"),
            year_built=year_built,
            floor=data.get("floor"),
            total_floors=data.get("total_floors"),
            document_type=data.get("document_type"),
            has_parking=data.get("has_parking", False),
            has_elevator=data.get("has_elevator", False),
            has_storage=data.get("has_storage", False),
            is_renovated=data.get("is_renovated", False),
            open_to_exchange=data.get("open_to_exchange", False),
            exchange_preferences=data.get("exchange_preferences", [])
        )

    def convert_to_property(
            self,
            submission: PropertySubmissionWithStatus
    ) -> Property:
        """change ads to property for show it"""
        try:
            property_type = PropertyType(submission.property_type) if submission.property_type else None
        except:
            property_type = None
            
        try:
            transaction_type = TransactionType(submission.transaction_type) if submission.transaction_type else None
        except:
            transaction_type = None
            
        try:
            document_type = DocumentType(submission.document_type) if submission.document_type else None
        except:
            document_type = None

        return Property(
            id=submission.id,
            title=submission.title or "",
            property_type=property_type,
            transaction_type=transaction_type,
            price=submission.price or 0,
            area=submission.area or 0,
            city=submission.city or "",
            district=submission.district or "",
            bedrooms=submission.bedrooms,
            year_built=submission.year_built,
            floor=submission.floor,
            total_floors=submission.total_floors,
            document_type=document_type,
            has_parking=submission.has_parking,
            has_elevator=submission.has_elevator,
            has_storage=submission.has_storage,
            is_renovated=submission.is_renovated,
            open_to_exchange=submission.open_to_exchange,
            exchange_preferences=submission.exchange_preferences,
            owner_phone=submission.owner_phone or "",
            description=submission.description or "",
        )

    def get_all_properties(self) -> List[Property]:
        """get all properties like object if approved"""
        submissions = self.get_all_submissions(status=PropertyStatus.APPROVED)
        return [self.convert_to_property(s) for s in submissions]

    def get_property_by_id(self, property_id: str) -> Optional[Property]:
        """get properties with id"""
        submission = self.get_submission(property_id)
        if submission:
            return self.convert_to_property(submission)
        return None

    def get_exchange_properties(self) -> List[Property]:
        """get properties ready for exchange"""
        try:
            # use filter for better performance
            results = database_service.select(
                "properties", 
                filters={
                    "status": "تایید_شده",
                    "open_to_exchange": True
                }
            )
            submissions = [self._map_db_to_submission(item) for item in results]
            return [self.convert_to_property(s) for s in submissions]
        except Exception as e:
            print(f" error to get reday to exchange amlac :  {e}")
            return []

    def get_statistics(self) -> Dict[str, Any]:
        """amar ads"""
        try:
            query = """
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN status = 'در_انتظار_تایید' THEN 1 END) as pending,
                    COUNT(CASE WHEN status = 'تایید_شده' THEN 1 END) as approved,
                    COUNT(CASE WHEN status = 'رد_شده' THEN 1 END) as rejected
                FROM properties
            """
            results = database_service.execute_raw(query)
            if results:
                return {
                    "total": results[0]["total"],
                    "pending": results[0]["pending"],
                    "approved": results[0]["approved"],
                    "rejected": results[0]["rejected"],
                }
            return {"total": 0, "pending": 0, "approved": 0, "rejected": 0}
        except Exception as e:
            print(f" error to get amlac amar : {e}")
            return {"total": 0, "pending": 0, "approved": 0, "rejected": 0}

    def update_property_details(self, property_id: str, updates: Dict) -> bool:
        """update amlac details"""
        try:
            if "exchange_preferences" in updates and isinstance(updates["exchange_preferences"], list):
                updates["exchange_preferences"] = json.dumps(updates["exchange_preferences"])

            updates['updated_at'] = datetime.now().isoformat()
            result = database_service.update("properties", property_id, updates)
            return bool(result)
        except Exception as e:
            print(f"error in update details of amlac :  {e}")
            return False

    def search_properties(
        self,
        city: Optional[str] = None,
        district: Optional[str] = None,
        property_type: Optional[str] = None,
        min_price: Optional[int] = None,
        max_price: Optional[int] = None,
        min_area: Optional[int] = None,
        max_area: Optional[int] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[PropertySubmissionWithStatus]:
        """Advanced Property Search"""
        try:
            # creat filter
            filters = {"status": "تایید_شده"}
            
            if city:
                filters["city"] = city
            if district:
                filters["district"] = district
            if property_type:
                filters["property_type"] = property_type
            
            #  get all result and filtered in python
            # in perfessional way we can create dynamic query
            results = database_service.select(
                "properties", 
                filters=filters,
                limit=limit,
                offset=offset
            )
            
            # numeric filter
            filtered_results = []
            for item in results:
                if min_price is not None and item.get("price", 0) < min_price:
                    continue
                if max_price is not None and item.get("price", 0) > max_price:
                    continue
                if min_area is not None and item.get("area", 0) < min_area:
                    continue
                if max_area is not None and item.get("area", 0) > max_area:
                    continue
                filtered_results.append(item)
            
            return [self._map_db_to_submission(item) for item in filtered_results]
        except Exception as e:
            print(f"error in searching amlack {e}")
            return []

# Instance for all
property_manager = PropertyManager()