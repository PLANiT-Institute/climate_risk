import { NextRequest, NextResponse } from "next/server";
import { assessmentData } from "../../_data/esg";

export async function GET(request: NextRequest) {
  const framework = request.nextUrl.searchParams.get("framework") || "tcfd";
  const data = assessmentData[framework];
  if (!data) {
    return NextResponse.json(
      { detail: `Unknown framework: ${framework}. Valid: ${Object.keys(assessmentData)}` },
      { status: 400 },
    );
  }
  return NextResponse.json(data);
}
