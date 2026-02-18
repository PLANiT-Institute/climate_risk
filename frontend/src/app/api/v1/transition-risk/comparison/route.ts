import { NextResponse } from "next/server";
import { comparisonData } from "../../_data/transition";

export async function GET() {
  return NextResponse.json(comparisonData);
}
