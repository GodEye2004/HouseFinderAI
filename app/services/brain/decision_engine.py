from app.models.property import Property, UserRequirements, PropertyScore, TransactionType
from typing import List, Dict, Tuple
from app.services.brain.scoring import PropertyScoringSystem
from app.services.advertisements.app_property.property_manager import property_manager



class DecisionEngine:
    """
    Main decision-making engine
    All decisions are made here, not by the LLM
    """

    def __init__(self):
        self.scoring_system = PropertyScoringSystem()

    def make_decision(
            self,
            properties: List[Property],
            requirements: UserRequirements
    ) -> Dict:
        """
        Make a decision based on the properties and user requirements.

        Returns:
            {
                'status': 'success' | 'no_results' | 'need_more_info',
                'properties': List[PropertyScore],
                'decision_summary': dict,
                'recommendations': list,
                'filters_applied': dict
            }
        """

        # Step 1: Checking the adequacy of information
        missing_critical = self._check_missing_critical_info(requirements)
        if missing_critical:
            return {
                'status': 'need_more_info',
                'missing_fields': missing_critical,
                'properties': [],
                'decision_summary': {},
                'recommendations': []
            }

        # Step 2: Filtering properties (hard decisions)
        filtered_properties, filters_applied = self._apply_hard_filters(
            properties,
            requirements
        )

        
        filtered_properties, filters_applied = self._apply_hard_filters(
            properties,
            requirements
        )

        # Step 3: Scoring properties (soft decisions)
        if not filtered_properties:
            # ----------------------------------------------------------------
            # Smart Search: If not found in destination city, check other cities
            # ----------------------------------------------------------------
            if filters_applied.get('city'):
                print("search in other city")
                # Copy of requirements without city
                relaxed_req = requirements.model_copy()
                relaxed_req.city = None

                # Re-filter without city
                global_props, _ = self._apply_hard_filters(properties, relaxed_req)
                
                if global_props:
                    # rank and find best matches
                    scored_global = self.scoring_system.rank_properties(global_props, relaxed_req)
                    
                    found_city = "شهرهای دیگر"
                    if scored_global:
                         p = property_manager.get_property_by_id(scored_global[0].property_id)
                         if p: found_city = p.city.strip()

                    return {
                        'status': 'success',
                        'city_mismatch': True,
                        'original_city': requirements.city,
                        'found_city': found_city,
                        'properties': scored_global,
                        'decision_summary': {
                            'reason': f'در {requirements.city} پیدا نشد، اما {len(global_props)} مورد در {found_city} پیدا شد.',
                            'is_global_fallback': True
                        },
                        'recommendations': [
                            f"در {requirements.city} ملکی با این مشخصات نداریم، اما این موارد در '{found_city}' کاملاً با بودجه شما سازگاره."
                        ]
                    }

            return {
                'status': 'no_results',
                'properties': [],
                'decision_summary': {
                    'total_checked': len(properties),
                    'filters_applied': filters_applied,
                    'reason': 'هیچ ملکی با فیلترهای الزامی شما مطابقت نداشت'
                },
                'recommendations': self._generate_relaxation_suggestions(
                    requirements,
                    filters_applied
                )
            }

        # scoring
        scored_properties = self.scoring_system.rank_properties(
            filtered_properties,
            requirements
        )

        # Step 4: Analyzing results and generating recommendations
        decision_summary = self._create_decision_summary(
            properties,
            filtered_properties,
            scored_properties,
            filters_applied,
            requirements
        )

        recommendations = self._generate_recommendations(
            scored_properties,
            requirements
        )

        return {
            'status': 'success',
            'properties': scored_properties,
            'decision_summary': decision_summary,
            'recommendations': recommendations,
            'filters_applied': filters_applied
        }

    def _check_missing_critical_info(self, req: UserRequirements) -> List[str]:
        """Check for missing critical information"""
        missing = []

        # If user specifies a district or transaction type (especially exchange), 
        # we can proceed even without a city (global search)
        if req.city is None and not (req.district or req.transaction_type):
            missing.append('city')
            
        return missing

    def _apply_hard_filters(
            self,
            properties: List[Property],
            req: UserRequirements
    ) -> Tuple[List[Property], Dict]:
        """
        Hard Filters (Complete Removal)
        This is where the hard decisions are made
        """

        filters_applied = {
            'budget': False,
            'city': False,
            'district': False,
            'property_type': False,
            'transaction_type': False,
            'area': False,
            'year_built': False,
            'document_type': False,
            'must_have_parking': False,
            'must_have_elevator': False,
            'must_have_storage': False,
            'must_be_exchange': False
        }

        filtered = properties

        # Exchange filter
        if req.wants_exchange:
            filtered = [p for p in filtered if p.open_to_exchange]
            filters_applied['must_be_exchange'] = True

        # Transaction Type Filter (Required)
        if req.transaction_type:
            # If user wants exchange, we also allow "SALE" properties that are open to exchange
            if req.wants_exchange:
                filtered = [
                    p for p in filtered
                    if p.transaction_type == req.transaction_type or 
                       (p.transaction_type == TransactionType.SALE and p.open_to_exchange)
                ]
            else:
                filtered = [
                    p for p in filtered
                    if p.transaction_type == req.transaction_type
                ]
            filters_applied['transaction_type'] = True

        # Budget Filter (Range)
        if req.budget_max:
            # Allow up to 10% more than the max budget
            budget_tolerance = int(req.budget_max * 1.1)
            filtered = [p for p in filtered if p.price <= budget_tolerance]
            filters_applied['budget'] = True

        if req.budget_min:
            # Strict minimum budget filter
            # (No downward tolerance by default, or maybe 5% for close matches)
            filtered = [p for p in filtered if p.price >= req.budget_min]
            filters_applied['budget'] = True

        # City Filter (Required)
        if req.city:
            target_city = req.city.strip().lower()
            filtered = [
                p for p in filtered
                if p.city and p.city.strip().lower() == target_city
            ]
            filters_applied['city'] = True

        # Region filter (if specified)
        if req.district:
            filtered = [
                p for p in filtered
                if p.district.lower() == req.district.lower()
            ]
            filters_applied['district'] = True

        # Property Type Filter (Optional - Only if specified by user)
        if req.property_type:
            filtered = [
                p for p in filtered
                if p.property_type == req.property_type
            ]
            filters_applied['property_type'] = True

        # Area Filter (with tolerance)
        if req.area_min:
            # Allow up to 20 sqm less than the minimum
            area_tolerance = max(0, req.area_min - 20)
            filtered = [p for p in filtered if p.area >= area_tolerance]
            filters_applied['area'] = True
            
        if req.area_max:
            # Allow up to 20 sqm more than the maximum
            area_max_tolerance = req.area_max + 20
            filtered = [p for p in filtered if p.area <= area_max_tolerance]
            filters_applied['area'] = True

        # Year Built Filter
        if req.year_built_min:
            filtered = [
                p for p in filtered
                if p.year_built and p.year_built >= req.year_built_min
            ]
            filters_applied['year_built'] = True

        # Document type filter
        if req.document_type:
            filtered = [
                p for p in filtered
                if p.document_type == req.document_type
            ]
            filters_applied['document_type'] = True

        # Required feature filters
        if req.must_have_parking:
            filtered = [p for p in filtered if p.has_parking]
            filters_applied['must_have_parking'] = True

        if req.must_have_elevator:
            filtered = [p for p in filtered if p.has_elevator]
            filters_applied['must_have_elevator'] = True

        if req.must_have_storage:
            filtered = [p for p in filtered if p.has_storage]
            filters_applied['must_have_storage'] = True

        return filtered, filters_applied

    def _create_decision_summary(
            self,
            all_properties: List[Property],
            filtered_properties: List[Property],
            scored_properties: List[PropertyScore],
            filters_applied: Dict,
            requirements: UserRequirements
    ) -> Dict:
        """Building a Decision Summary"""

        # Number of properties removed at each stage
        filters_stats = {}
        temp_props = all_properties

        for filter_name, applied in filters_applied.items():
            if applied:
                before_count = len(temp_props)
                # Apply filter for stats
                temp_props = self._apply_single_filter(
                    temp_props,
                    filter_name,
                    requirements
                )
                after_count = len(temp_props)
                filters_stats[filter_name] = {
                    'removed': before_count - after_count,
                    'remaining': after_count
                }

        # Best and worst match
        best_match = scored_properties[0] if scored_properties else None
        worst_match = scored_properties[-1] if scored_properties else None

        return {
            'total_properties_checked': len(all_properties),
            'properties_after_filtering': len(filtered_properties),
            'properties_scored': len(scored_properties),
            'filters_stats': filters_stats,
            'best_match_percentage': best_match.match_percentage if best_match else 0,
            'worst_match_percentage': worst_match.match_percentage if worst_match else 0,
            'average_match': sum(p.match_percentage for p in scored_properties) / len(
                scored_properties) if scored_properties else 0
        }

    def _generate_recommendations(
            self,
            scored_properties: List[PropertyScore],
            requirements: UserRequirements
    ) -> List[str]:
        """Generating recommendations from the decision engine"""

        recommendations = []

        if not scored_properties:
            return []

        best = scored_properties[0]

        # Recommendations based on score
        if best.match_percentage >= 90:
            recommendations.append("ملک شماره 1 تطابق فوق‌العاده‌ای با نیاز شما دارد")
        elif best.match_percentage >= 75:
            recommendations.append("ملک شماره 1 انتخاب خوبی است")
        elif best.match_percentage >= 60:
            recommendations.append("املاک پیدا شده تا حدودی مناسب هستند، ممکن است نیاز به تسامح در برخی معیارها باشد")
        else:
            recommendations.append("هیچ ملک بسیار مناسبی پیدا نشد، پیشنهاد می‌شود معیارها را تغییر دهید")

        if scored_properties:
            prices = []
            for score in scored_properties[:5]:
                prop = property_manager.get_property_by_id(score.property_id)

                if prop:
                    prices.append(prop.price)

            if prices:
                avg_price = sum(prices) / len(prices)
                if requirements.budget_max:
                    price_ratio = avg_price / requirements.budget_max
                    if price_ratio < 0.7:
                        recommendations.append(
                            "املاک پیدا شده ارزان‌تر از بودجه شما هستند، می‌توانید گزینه‌های بهتری جستجو کنید")
                    elif price_ratio > 0.95:
                        recommendations.append("املاک نزدیک به سقف بودجه شما هستند")

        # Recommendation based on number of results
        if len(scored_properties) < 3:
            recommendations.append("تعداد نتایج کم است، شاید بتوان معیارها را کمی انعطاف‌پذیرتر کرد")
        elif len(scored_properties) > 10:
            recommendations.append("تعداد زیادی ملک مناسب پیدا شد، می‌توانید فیلترهای بیشتری اضافه کنید")

        return recommendations

    def _generate_relaxation_suggestions(
            self,
            requirements: UserRequirements,
            filters_applied: Dict
    ) -> List[str]:
        """Generating relaxation suggestions"""

        suggestions = []

        if filters_applied.get('district'):
            suggestions.append("محدودیت منطقه را حذف کنید و کل شهر را جستجو کنید")

        if filters_applied.get('year_built'):
            suggestions.append("محدودیت سال ساخت را کاهش دهید")

        if filters_applied.get('document_type'):
            suggestions.append("انواع مختلف سند را بپذیرید")

        if filters_applied.get('must_have_storage'):
            suggestions.append("شرط داشتن انباری را حذف کنید")

        if requirements.budget_max:
            new_budget = int(requirements.budget_max * 1.2)
            suggestions.append(f"بودجه را تا {new_budget:,} تومان افزایش دهید")

        return suggestions

    def _apply_single_filter(
            self,
            properties: List[Property],
            filter_name: str,
            req: UserRequirements
    ) -> List[Property]:
        """اعمال یک فیلتر برای محاسبه آمار"""

        if filter_name == 'budget':
            res = properties
            if req.budget_max:
                res = [p for p in res if p.price <= req.budget_max]
            if req.budget_min:
                res = [p for p in res if p.price >= req.budget_min]
            return res
        elif filter_name == 'city' and req.city:
            return [p for p in properties if p.city.lower() == req.city.lower()]
        elif filter_name == 'district' and req.district:
            return [p for p in properties if p.district.lower() == req.district.lower()]
        elif filter_name == 'property_type' and req.property_type:
            return [p for p in properties if p.property_type == req.property_type]
        elif filter_name == 'area' and req.area_min:
            return [p for p in properties if p.area >= req.area_min]
        elif filter_name == 'year_built' and req.year_built_min:
            return [p for p in properties if p.year_built and p.year_built >= req.year_built_min]
        elif filter_name == 'must_have_parking':
            return [p for p in properties if p.has_parking]
        elif filter_name == 'must_have_elevator':
            return [p for p in properties if p.has_elevator]
        elif filter_name == 'must_have_storage':
            return [p for p in properties if p.has_storage]

        return properties