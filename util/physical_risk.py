from climada.hazard import RiverFlood
from climada.exposures import Exposures
from climada_petals import ImpactFuncSetFlood
from climada.impact import ImpactCalc
import pandas as pd

class PhysicalRisk:
    def __init__(self, facilities_df, hazard_file_path):
        self.facilities_df = facilities_df
        self.hazard_file_path = hazard_file_path
        # 국가 코드에서 지역(영향 함수 레이블)으로 매핑
        self.country_to_region = {
            'DEU': 'RF3',  # 독일, 유럽
            'USA': 'RF4',  # 미국, 북미
            # 필요에 따라 더 추가
        }

    def _get_impf_label(self, country_code):
        if country_code in self.country_to_region:
            return self.country_to_region[country_code]
        else:
            raise ValueError(f"국가 코드 {country_code}가 어떤 지역에도 매핑되지 않았습니다.")

    def run(self):
        # 노출 데이터 로드
        exposure = Exposures()
        for index, row in self.facilities_df.iterrows():
            impf_label = self._get_impf_label(row['country_code'])
            exposure.add(
                lat=row['latitude'],
                lon=row['longitude'],
                value=row['asset_value'],
                impf_label=impf_label,
                id=row['facility_id']
            )

        # 위험 데이터 로드
        hazard = RiverFlood()
        hazard.from_nc(self.hazard_file_path)

        # 홍수에 대한 영향 함수 세트 로드
        impf_set = ImpactFuncSetFlood()

        # 영향 계산
        impact_calc = ImpactCalc()
        impact_calc.set_hazard(hazard)
        impact_calc.set_exposure(exposure)
        impact_calc.set_impf_set(impf_set)
        impact_df = impact_calc.compute()

        # 각 시설에 대한 연간 예상 손실 계산
        impact_df['weighted_loss'] = impact_df['loss'] * impact_df['event_id'].apply(lambda x: hazard.freq[x])
        annual_flood_loss = impact_df.groupby('exp_id')['weighted_loss'].sum().reset_index()
        annual_flood_loss.columns = ['facility_id', 'annual_flood_loss']

        return annual_flood_loss