import { NextResponse } from "next/server";
import { scenariosData } from "../_data/scenarios";

export async function GET() {
  return NextResponse.json(scenariosData);
}
