import { NextRequest, NextResponse } from "next/server";
import { analysisData } from "../../_data/transition";

export async function GET(request: NextRequest) {
  const scenario = request.nextUrl.searchParams.get("scenario") || "current_policies";
  const data = analysisData[scenario];
  if (!data) {
    return NextResponse.json(
      { detail: `Unknown scenario: ${scenario}. Valid: ${Object.keys(analysisData)}` },
      { status: 400 },
    );
  }
  return NextResponse.json(data);
}
