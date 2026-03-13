import { NextRequest, NextResponse } from "next/server";
import { updatePrescription, type MedicinePrice } from "@/lib/dummy-data";
import { lookupMedicinePrice } from "@/lib/scrapegraph";

export async function POST(request: NextRequest) {
  const { medicines, country, prescriptionId } = await request.json();

  if (!medicines || !Array.isArray(medicines) || medicines.length === 0) {
    return NextResponse.json({ error: "medicines array is required" }, { status: 400 });
  }

  const targetCountry = country || "USA";

  // Look up all medicines in parallel
  const results = await Promise.allSettled(
    medicines.map((med: string) => lookupMedicinePrice(med, targetCountry))
  );

  const allResults: MedicinePrice[] = results.flatMap((r) =>
    r.status === "fulfilled" ? r.value : []
  );

  // Save to prescription if ID provided
  if (prescriptionId) {
    updatePrescription(prescriptionId, {
      priceLookupResults: allResults,
      priceLookupCompleted: true,
    });
  }

  return NextResponse.json({ results: allResults });
}
