import { NextRequest, NextResponse } from "next/server";
import { getPrescriptionById, updatePrescription } from "@/lib/dummy-data";

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;

  const prescription = getPrescriptionById(id);
  if (!prescription) {
    return NextResponse.json({ error: "Prescription not found" }, { status: 404 });
  }

  return NextResponse.json({ prescription });
}

export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const body = await request.json();

  const prescription = updatePrescription(id, body);
  if (!prescription) {
    return NextResponse.json({ error: "Prescription not found" }, { status: 404 });
  }

  return NextResponse.json({ prescription });
}
