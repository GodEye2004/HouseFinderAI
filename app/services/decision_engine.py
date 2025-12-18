from app.models.property import Property, UserRequirements, PropertyScore
from typing import List, Dict, Tuple
from app.services.scoring import PropertyScoringSystem
from app.services.property_manager import property_manager



class DecisionEngine:
    """
    موتور تصمیم‌گیری اصلی
    همه تصمیمات در اینجا گرفته می‌شود، نه توسط LLM
    """

    def __init__(self):
        self.scoring_system = PropertyScoringSystem()

    def make_decision(
            self,
            properties: List[Property],
            requirements: UserRequirements
    ) -> Dict:
        """
        تصمیم‌گیری کامل و بازگشت نتایج ساختاری

        Returns:
            {
                'status': 'success' | 'no_results' | 'need_more_info',
                'properties': List[PropertyScore],
                'decision_summary': dict,
                'recommendations': list,
                'filters_applied': dict
            }
        """

        # مرحله 1: بررسی کفایت اطلاعات
        missing_critical = self._check_missing_critical_info(requirements)
        if missing_critical:
            return {
                'status': 'need_more_info',
                'missing_fields': missing_critical,
                'properties': [],
                'decision_summary': {},
                'recommendations': []
            }

        # مرحله 2: فیلتر کردن املاک (تصمیمات سخت)
        filtered_properties, filters_applied = self._apply_hard_filters(
            properties,
            requirements
        )

        # مرحله 2: فیلتر کردن املاک (تصمیمات سخت)
        filtered_properties, filters_applied = self._apply_hard_filters(
            properties,
            requirements
        )

        # مرحله 3: امتیازدهی به املاک (تصمیمات نرم)
        if not filtered_properties:
            # ----------------------------------------------------------------
            # جستجوی هوشمند: اگر در شهر مقصد نبود، شهرهای دیگر را چک کن
            # ----------------------------------------------------------------
            if filters_applied.get('city'):
                print("   🌍 جستجو در سایر شهرها...")
                # کپی از requirements بدون شهر
                relaxed_req = requirements.copy()
                relaxed_req.city = None
                
                # فیلتر مجدد بدون شهر
                global_props, _ = self._apply_hard_filters(properties, relaxed_req)
                
                if global_props:
                    # پیدا شد!
                    scored_global = self.scoring_system.rank_properties(global_props, relaxed_req)
                    best_global = scored_global[0] if scored_global else None
                    
                    found_city = "شهرهای دیگر"
                    if best_global:
                         p = property_manager.get_property_by_id(best_global.property_id)
                         if p: found_city = p.city.strip()

                    return {
                        'status': 'no_results',
                        'properties': [],
                        'decision_summary': {
                            'reason': f'در {requirements.city} پیدا نشد، اما {len(global_props)} مورد در {found_city} پیدا شد.'
                        },
                        'recommendations': [
                            f"در {requirements.city} ملکی نداریم، اما در '{found_city}' موارد مشابهی با بودجه شما موجود است."
                        ] + self._generate_relaxation_suggestions(requirements, filters_applied)
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

        # امتیازدهی
        scored_properties = self.scoring_system.rank_properties(
            filtered_properties,
            requirements
        )

        # مرحله 4: تحلیل نتایج و تولید توصیه‌ها
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
        """بررسی اطلاعات حیاتی"""
        missing = []

        # فقط شهر الزامی است تا بتوانیم لیست بدهیم
        if req.city is None:
            missing.append('city')
            
        return missing

    def _apply_hard_filters(
            self,
            properties: List[Property],
            req: UserRequirements
    ) -> Tuple[List[Property], Dict]:
        """
        فیلترهای سخت (حذف کامل)
        اینجا تصمیمات قاطع گرفته می‌شود
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
            'must_have_storage': False
        }

        filtered = properties

        # فیلتر نوع معامله (الزامی)
        if req.transaction_type:
            filtered = [
                p for p in filtered
                if p.transaction_type == req.transaction_type
            ]
            filters_applied['transaction_type'] = True

        # فیلتر بودجه (با تلرانس 10%)
        if req.budget_max:
            # اجازه می‌دهیم تا 10% بیشتر از بودجه را هم نشان دهیم
            budget_tolerance = int(req.budget_max * 1.1)
            filtered = [p for p in filtered if p.price <= budget_tolerance]
            filters_applied['budget'] = True

        # فیلتر شهر (الزامی)
        if req.city:
            target_city = req.city.strip().lower()
            filtered = [
                p for p in filtered
                if p.city and p.city.strip().lower() == target_city
            ]
            filters_applied['city'] = True

        # فیلتر منطقه (اگر مشخص شده)
        if req.district:
            filtered = [
                p for p in filtered
                if p.district.lower() == req.district.lower()
            ]
            filters_applied['district'] = True

        # فیلتر نوع ملک (اختیاری - فقط اگر کاربر مشخص کرده)
        if req.property_type:
            filtered = [
                p for p in filtered
                if p.property_type == req.property_type
            ]
            filters_applied['property_type'] = True

        # فیلتر متراژ (با تلرانس)
        if req.area_min:
            # اجازه می‌دهیم تا 20 متر کمتر از حداقل را هم نشان دهیم
            area_tolerance = max(0, req.area_min - 20)
            filtered = [p for p in filtered if p.area >= area_tolerance]
            filters_applied['area'] = True
            
        if req.area_max:
            # اجازه می‌دهیم تا 20 متر بیشتر از حداکثر را هم نشان دهیم
            area_max_tolerance = req.area_max + 20
            filtered = [p for p in filtered if p.area <= area_max_tolerance]
            filters_applied['area'] = True

        # فیلتر سال ساخت
        if req.year_built_min:
            filtered = [
                p for p in filtered
                if p.year_built and p.year_built >= req.year_built_min
            ]
            filters_applied['year_built'] = True

        # فیلتر نوع سند
        if req.document_type:
            filtered = [
                p for p in filtered
                if p.document_type == req.document_type
            ]
            filters_applied['document_type'] = True

        # فیلترهای امکانات الزامی
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
        """ساخت خلاصه تصمیم"""

        # تعداد املاک حذف شده در هر مرحله
        filters_stats = {}
        temp_props = all_properties

        for filter_name, applied in filters_applied.items():
            if applied:
                before_count = len(temp_props)
                # شبیه‌سازی فیلتر برای آمار
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

        # بهترین و بدترین تطابق
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
        """تولید توصیه‌های موتور تصمیم"""

        recommendations = []

        if not scored_properties:
            return []

        best = scored_properties[0]

        # توصیه بر اساس امتیاز
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

        # توصیه بر اساس تعداد نتایج
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
        """پیشنهاد کاهش محدودیت‌ها"""

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

        if filter_name == 'budget' and req.budget_max:
            return [p for p in properties if p.price <= req.budget_max]
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