import { NextResponse } from "next/server";
import { facilitiesData } from "../../_data/facilities";

export async function GET() {
  return NextResponse.json(facilitiesData);
}
