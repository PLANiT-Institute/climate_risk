import { NextResponse } from "next/server";
import { frameworksData } from "../../_data/esg";

export async function GET() {
  return NextResponse.json(frameworksData);
}
