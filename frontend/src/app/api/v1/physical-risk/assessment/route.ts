import { NextResponse } from "next/server";
import { physicalRiskData } from "../../_data/physical";

export async function GET() {
  return NextResponse.json(physicalRiskData);
}
