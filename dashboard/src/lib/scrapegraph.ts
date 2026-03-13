const SCRAPEGRAPH_API_KEY = process.env.SCRAPEGRAPH_API_KEY;

export interface MedicinePriceResult {
  medicine: string;
  pharmacy: string;
  price: string;
  currency: string;
  address: string;
  distance: string;
  available: boolean;
  mapLink: string;
}

export async function lookupMedicinePrice(
  medicine: string,
  country: string
): Promise<MedicinePriceResult[]> {
  const searchQuery = `${medicine} price pharmacy ${country}`;

  const response = await fetch("https://api.scrapegraphai.com/v1/smartscraper", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "SGAI-APIKEY": SCRAPEGRAPH_API_KEY || "",
    },
    body: JSON.stringify({
      website_url: `https://www.google.com/search?q=${encodeURIComponent(searchQuery)}`,
      user_prompt: `Find pharmacies selling ${medicine} in ${country}. For each result, extract: pharmacy name, price with currency, address, and whether it is available. Return as a JSON array with objects having fields: pharmacy, price, currency, address, available (boolean). Return at most 5 results.`,
    }),
  });

  if (!response.ok) {
    throw new Error(`ScrapeGraph API error: ${response.status}`);
  }

  const data = await response.json();

  // Parse results - ScrapeGraph returns varied formats
  const resultText = typeof data.result === "string" ? data.result : JSON.stringify(data.result);

  try {
    const parsed = JSON.parse(resultText);
    const items = Array.isArray(parsed) ? parsed : [parsed];

    return items.map((item: any) => ({
      medicine,
      pharmacy: item.pharmacy || item.name || "Local Pharmacy",
      price: item.price || "Price unavailable",
      currency: item.currency || "USD",
      address: item.address || item.location || "",
      distance: item.distance || "",
      available: item.available !== false,
      mapLink: item.address
        ? `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(item.address)}`
        : "",
    }));
  } catch {
    // Fallback if parsing fails
    return [
      {
        medicine,
        pharmacy: "Search Result",
        price: resultText.slice(0, 200),
        currency: "",
        address: "",
        distance: "",
        available: true,
        mapLink: "",
      },
    ];
  }
}
