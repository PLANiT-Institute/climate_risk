"""Standalone address-to-coordinates converter.

Usage:
    python sandbox/geocode.py

Enter an address when prompted. The script prints the latitude/longitude
and a ready-to-paste snippet for sample_facilities.py.
"""

from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError


def geocode_address(address: str) -> tuple[float, float] | None:
    """Convert an address string to (latitude, longitude).

    Args:
        address: Street address or place name (Korean or English).

    Returns:
        (latitude, longitude) tuple, or None if not found.
    """
    geolocator = Nominatim(user_agent="climate_risk_sandbox")
    try:
        location = geolocator.geocode(address, timeout=10)
    except GeocoderTimedOut:
        print("오류: 서버 응답 시간 초과. 다시 시도해주세요.")
        return None
    except GeocoderServiceError as e:
        print(f"오류: 지오코딩 서비스 오류 — {e}")
        return None

    if location is None:
        print("주소를 찾을 수 없습니다. 더 구체적으로 입력해보세요.")
        return None

    return location.latitude, location.longitude


def main() -> None:
    print("=" * 50)
    print("  주소 → 위도/경도 변환기")
    print("  종료하려면 Ctrl+C 를 누르세요")
    print("=" * 50)

    while True:
        print()
        try:
            address = input("주소를 입력하세요: ").strip()
        except KeyboardInterrupt:
            print("\n종료합니다.")
            break
        if not address:
            continue

        result = geocode_address(address)
        if result is None:
            continue

        lat, lon = result
        print()
        print("-" * 40)
        print(f"주소  : {address}")
        print(f"위도  : {lat:.6f}")
        print(f"경도  : {lon:.6f}")
        print()
        print("sample_facilities.py 에 붙여넣을 값:")
        print(f'    "latitude": {lat:.6f},')
        print(f'    "longitude": {lon:.6f},')
        print("-" * 40)


if __name__ == "__main__":
    main()
