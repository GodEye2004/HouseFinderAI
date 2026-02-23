from app.models.property import Property, UserRequirements, PropertyScore
from typing import List
import math


class PropertyScoringSystem:
    """Real estate scoring system based on user needs"""

    # Weights for variables (must sum to 100)
    WEIGHTS = {
        "price": 30,  # Required
        "area": 20,  # Required
        "location": 15,  # Required (City + District)
        "property_type": 10,  # Required
        "bedrooms": 10,  # Important
        "age": 5,  # Important
        "floor": 3,  # Optional
        "parking": 3,  # Optional
        "elevator": 2,  # Optional
        "storage": 1,  # Optional
        "renovated": 1,  # Optional
    }

    def __init__(self):
        self.total_weight = sum(self.WEIGHTS.values())

    def calculate_score(self, property: Property, requirements: UserRequirements) -> PropertyScore:
        """Calculate the overall score of a property"""
        scores = {}
        missing = []

        # Price score
        price_score, price_missing = self._score_price(property, requirements)
        scores["price"] = price_score
        if price_missing:
            missing.append(price_missing)

        # Area score
        area_score, area_missing = self._score_area(property, requirements)
        scores["area"] = area_score
        if area_missing:
            missing.append(area_missing)

        # Location score
        location_score, location_missing = self._score_location(property, requirements)
        scores["location"] = location_score
        if location_missing:
            missing.extend(location_missing)

        # Property type score
        type_score = self._score_property_type(property, requirements)
        scores["property_type"] = type_score

        # Bedrooms score
        bedrooms_score = self._score_bedrooms(property, requirements)
        scores["bedrooms"] = bedrooms_score

        # Age score
        age_score = self._score_age(property, requirements)
        scores["age"] = age_score

        # Floor score
        floor_score = self._score_floor(property, requirements)
        scores["floor"] = floor_score

        # Facilities score
        parking_score = self._score_parking(property, requirements)
        elevator_score = self._score_elevator(property, requirements)
        storage_score = self._score_storage(property, requirements)
        renovated_score = self._score_renovated(property, requirements)

        scores["parking"] = parking_score
        scores["elevator"] = elevator_score
        scores["storage"] = storage_score
        scores["renovated"] = renovated_score

        # Calculating the final score
        total_score = sum(scores.values())
        match_percentage = (total_score / self.total_weight) * 100

        return PropertyScore(
            property_id=property.id,
            total_score=round(total_score, 2),
            score_details=scores,
            match_percentage=round(match_percentage, 2),
            missing_requirements=missing
        )

    def _score_price(self, property: Property, req: UserRequirements):
        """Price scoring"""
        weight = self.WEIGHTS["price"]

        if req.budget_min is None and req.budget_max is None:
            return 0, "Budget not specified"

        price = property.price

        # If only maximum budget is specified
        if req.budget_max and req.budget_min is None:
            if price <= req.budget_max:
                ratio = price / req.budget_max
                return weight * (1 - ratio * 0.2), None  # The cheaper, the better
            else:
                return 0, None

        # If only minimum budget is specified
        if req.budget_min and req.budget_max is None:
            if price >= req.budget_min:
                return weight, None
            else:
                return weight * 0.5, None

        # If we have both
        if req.budget_min and req.budget_max:
            if req.budget_min <= price <= req.budget_max:
                mid = (req.budget_min + req.budget_max) / 2
                distance = abs(price - mid)
                range_size = req.budget_max - req.budget_min
                score_ratio = 1 - (distance / max(range_size, 1)) * 0.2
                return weight * score_ratio, None
            elif price < req.budget_min:
                # Heavy penalty for being below range
                ratio = price / req.budget_min
                if ratio < 0.5: return 0, None
                return weight * (ratio * 0.4), None # Max 40% of weight if just below
            else:
                # Penalty for being above range
                ratio = req.budget_max / price
                return weight * (ratio * 0.5), None

        return 0, "بودجه مشخص نشده"

    def _score_area(self, property: Property, req: UserRequirements):
        """Area scoring"""
        weight = self.WEIGHTS["area"]

        if req.area_min is None and req.area_max is None:
            return weight * 0.5, "متراژ مشخص نشده"

        area = property.area

        if req.area_max and req.area_min is None:
            if area <= req.area_max:
                return weight, None
            else:
                return weight * 0.3, None

        if req.area_min and req.area_max is None:
            if area >= req.area_min:
                return weight, None
            else:
                return weight * 0.3, None

        if req.area_min and req.area_max:
            if req.area_min <= area <= req.area_max:
                return weight, None
            elif area < req.area_min:
                return weight * 0.5, None
            else:
                return weight * 0.3, None

        return weight * 0.5, "متراژ مشخص نشده"

    def _score_location(self, property: Property, req: UserRequirements):
        """Positional Scoring"""
        weight = self.WEIGHTS["location"]
        missing = []

        city_match = False
        district_match = False

        if req.city is None:
            missing.append("شهر مشخص نشده")
        else:
            city_match = (property.city.lower() == req.city.lower())

        if req.district is None:
            missing.append("منطقه مشخص نشده")
        else:
            district_match = (property.district.lower() == req.district.lower())

        if city_match and district_match:
            return weight, []
        elif city_match:
            return weight * 0.7, missing
        elif district_match:
            return weight * 0.5, missing
        else:
            if missing:
                return weight * 0.3, missing
            else:
                return 0, []

    def _score_property_type(self, property: Property, req: UserRequirements):
        """Scoring by property type"""
        weight = self.WEIGHTS["property_type"]

        if req.property_type is None:
            return weight * 0.5

        if property.property_type == req.property_type:
            return weight
        else:
            return 0

    def _score_bedrooms(self, property: Property, req: UserRequirements):
        """Bedrooms scoring"""
        weight = self.WEIGHTS["bedrooms"]

        if req.bedrooms_min is None or property.bedrooms is None:
            return weight * 0.5

        if property.bedrooms >= req.bedrooms_min:
            return weight
        else:
            return weight * 0.3

    def _score_age(self, property: Property, req: UserRequirements):
        """Building age scoring"""
        weight = self.WEIGHTS["age"]

        if req.max_age is None or property.age is None:
            return weight * 0.5

        if property.age <= req.max_age:
            score_ratio = 1 - (property.age / req.max_age) * 0.3
            return weight * score_ratio
        else:
            return weight * 0.2

    def _score_floor(self, property: Property, req: UserRequirements):
        """Floor scoring"""
        weight = self.WEIGHTS["floor"]

        if req.min_floor is None or property.floor is None:
            return weight * 0.5

        if property.floor >= req.min_floor:
            return weight
        else:
            return weight * 0.3

    def _score_parking(self, property: Property, req: UserRequirements):
        """Parking scoring"""
        weight = self.WEIGHTS["parking"]

        if req.must_have_parking and property.has_parking:
            return weight
        elif req.must_have_parking and not property.has_parking:
            return 0
        elif property.has_parking:
            return weight
        else:
            return weight * 0.5

    def _score_elevator(self, property: Property, req: UserRequirements):
        """Elevator scoring"""
        weight = self.WEIGHTS["elevator"]

        if req.must_have_elevator and property.has_elevator:
            return weight
        elif req.must_have_elevator and not property.has_elevator:
            return 0
        elif property.has_elevator:
            return weight
        else:
            return weight * 0.5

    def _score_storage(self, property: Property, req: UserRequirements):
        """Storage scoring"""
        weight = self.WEIGHTS["storage"]
        return weight if property.has_storage else weight * 0.5

    def _score_renovated(self, property: Property, req: UserRequirements):
        """Renovated scoring"""
        weight = self.WEIGHTS["renovated"]
        return weight if property.is_renovated else weight * 0.5

    def rank_properties(self, properties: List[Property], requirements: UserRequirements) -> List[PropertyScore]:
        """Property ranking"""
        scores = [self.calculate_score(prop, requirements) for prop in properties]
        return sorted(scores, key=lambda x: x.total_score, reverse=True)