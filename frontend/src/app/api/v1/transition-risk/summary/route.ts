import { NextRequest, NextResponse } from "next/server";
import { summaryData } from "../../_data/transition";

export async function GET(request: NextRequest) {
  const scenario = request.nextUrl.searchParams.get("scenario") || "current_policies";
  const data = summaryData[scenario];
  if (!data) {
    return NextResponse.json(
      { detail: `Unknown scenario: ${scenario}. Valid: ${Object.keys(summaryData)}` },
      { status: 400 },
    );
  }
  return NextResponse.json(data);
}
