import OpenAI from "openai";

const SCRAPEGRAPH_API_KEY = process.env.SCRAPEGRAPH_API_KEY;

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

export interface MedicinePriceResult {
  medicine: string;
  pharmacy: string;
  price: string;
  currency: string;
  address: string;
  distance: string;
  available: boolean;
  mapLink: string;
  phoneNumber: string;
  openingHours: string;
  prescriptionRequired: boolean;
  genericAlternative: string;
  genericPrice: string;
  deliveryAvailable: boolean;
  pharmacyType: string;
  dosageMatch: string;
}

// Map common countries to their local currency
const COUNTRY_CURRENCY: Record<string, string> = {
  mexico: "MXN",
  usa: "USD",
  "united states": "USD",
  canada: "CAD",
  brazil: "BRL",
  colombia: "COP",
  argentina: "ARS",
  peru: "PEN",
  chile: "CLP",
  india: "INR",
  uk: "GBP",
  "united kingdom": "GBP",
  germany: "EUR",
  france: "EUR",
  spain: "EUR",
  japan: "JPY",
  china: "CNY",
  australia: "AUD",
  guatemala: "GTQ",
  honduras: "HNL",
  "el salvador": "USD",
  haiti: "HTG",
  "dominican republic": "DOP",
  nigeria: "NGN",
  kenya: "KES",
  philippines: "PHP",
};

function getLocalCurrency(country: string): string {
  return COUNTRY_CURRENCY[country.toLowerCase()] || "USD";
}

function parseResults(items: any[], medicine: string, localCurrency: string): MedicinePriceResult[] {
  return items.map((item: any) => ({
    medicine,
    pharmacy: item.pharmacy || item.name || "Local Pharmacy",
    price: item.price || "Price unavailable",
    currency: item.currency || localCurrency,
    address: item.address || item.location || "",
    distance: item.distance || "",
    available: item.available !== false,
    mapLink: item.address
      ? `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(item.address)}`
      : "",
    phoneNumber: item.phoneNumber || item.phone || "",
    openingHours: item.openingHours || item.hours || "",
    prescriptionRequired: item.prescriptionRequired === true,
    genericAlternative: item.genericAlternative || "",
    genericPrice: item.genericPrice || "",
    deliveryAvailable: item.deliveryAvailable === true,
    pharmacyType: item.pharmacyType || "",
    dosageMatch: item.dosageMatch || "",
  }));
}

// Primary: ScrapeGraph API
async function lookupViaScrapeGraph(
  medicine: string,
  zipcode: string,
  country: string,
  localCurrency: string
): Promise<MedicinePriceResult[]> {
  const searchQuery = `${medicine} price pharmacy near ${zipcode} ${country}`;

  const response = await fetch("https://api.scrapegraphai.com/v1/smartscraper", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "SGAI-APIKEY": SCRAPEGRAPH_API_KEY || "",
    },
    body: JSON.stringify({
      website_url: `https://www.google.com/search?q=${encodeURIComponent(searchQuery)}`,
      user_prompt: `Find pharmacies selling ${medicine} near zipcode ${zipcode} in ${country}. All prices MUST be in the local currency of ${country} which is ${localCurrency}. If prices are found in a different currency, convert them to ${localCurrency}.

For each pharmacy result, extract ALL of the following fields:
- pharmacy: pharmacy name
- price: price in local currency ${localCurrency} with the currency symbol (e.g. "$150.00 MXN" for Mexico, "$12.50 USD" for USA)
- currency: "${localCurrency}"
- address: full street address
- phoneNumber: phone number of the pharmacy
- openingHours: operating hours (e.g. "Mon-Fri 8am-9pm, Sat 9am-6pm")
- available: whether the medicine is in stock (true/false)
- prescriptionRequired: whether a prescription is needed to buy this medicine (true/false)
- genericAlternative: name of a cheaper generic equivalent if one exists (e.g. "Metformin" for "Glucophage"), or empty string if none
- genericPrice: price of the generic alternative in ${localCurrency}, or empty string
- deliveryAvailable: whether the pharmacy offers delivery (true/false)
- pharmacyType: one of "chain", "independent", or "hospital"
- dosageMatch: whether the exact prescribed dosage is available (e.g. "500mg - exact match" or "250mg only")

Return as a JSON array of objects. Return at most 5 results. If a field is unknown, use empty string for strings and false for booleans.`,
    }),
  });

  if (!response.ok) {
    const errBody = await response.text();
    throw new Error(`ScrapeGraph API error ${response.status}: ${errBody}`);
  }

  const data = await response.json();
  if (data.error) {
    throw new Error(`ScrapeGraph error: ${data.error}`);
  }

  const resultText = typeof data.result === "string" ? data.result : JSON.stringify(data.result);
  const parsed = JSON.parse(resultText);
  const items = Array.isArray(parsed) ? parsed : [parsed];
  return parseResults(items, medicine, localCurrency);
}

// Fallback: OpenAI
async function lookupViaOpenAI(
  medicine: string,
  zipcode: string,
  country: string,
  localCurrency: string
): Promise<MedicinePriceResult[]> {
  console.log(`[PriceLookup] ScrapeGraph failed, falling back to OpenAI for ${medicine}`);

  const response = await openai.chat.completions.create({
    model: "gpt-4o-mini",
    max_tokens: 1500,
    messages: [
      {
        role: "system",
        content: "You are a pharmacy pricing assistant. Use your knowledge of real pharmacy chains, real medication pricing, and real addresses to provide accurate pharmacy information. Always respond with valid JSON only, no markdown.",
      },
      {
        role: "user",
        content: `Find real pharmacies selling ${medicine} near zipcode ${zipcode} in ${country}. All prices must be in ${localCurrency}.

Return a JSON array of 3-5 pharmacy results. Each object must have these exact fields:
{
  "pharmacy": "real pharmacy chain name in ${country}",
  "price": "price with currency symbol in ${localCurrency}",
  "currency": "${localCurrency}",
  "address": "realistic full street address near zipcode ${zipcode}",
  "phoneNumber": "local phone number format",
  "openingHours": "typical hours like Mon-Fri 8am-9pm, Sat 9am-6pm",
  "available": true,
  "prescriptionRequired": true or false based on the medicine,
  "genericAlternative": "generic name if exists, or empty string",
  "genericPrice": "generic price in ${localCurrency} if available, or empty string",
  "deliveryAvailable": true or false,
  "pharmacyType": "chain" or "independent" or "hospital",
  "dosageMatch": "dosage availability info"
}

Use real pharmacy chains that exist in ${country} (e.g. Farmacias Guadalajara, Farmacias del Ahorro, Farmacia Benavides for Mexico; CVS, Walgreens, Walmart for USA). Use realistic pricing for ${country}.`,
      },
    ],
  });

  const text = response.choices[0]?.message?.content || "[]";
  const cleaned = text.replace(/```json\s*\n?/g, "").replace(/```\s*$/g, "").trim();
  const parsed = JSON.parse(cleaned);
  const items = Array.isArray(parsed) ? parsed : [parsed];
  return parseResults(items, medicine, localCurrency);
}

function priceUnavailableResult(medicine: string, localCurrency: string): MedicinePriceResult {
  return {
    medicine,
    pharmacy: "Lookup unavailable",
    price: "Price unavailable",
    currency: localCurrency,
    address: "",
    distance: "",
    available: false,
    mapLink: "",
    phoneNumber: "",
    openingHours: "",
    prescriptionRequired: false,
    genericAlternative: "",
    genericPrice: "",
    deliveryAvailable: false,
    pharmacyType: "",
    dosageMatch: "",
  };
}

// Main export: tries ScrapeGraph first, falls back to OpenAI
export async function lookupMedicinePrice(
  medicine: string,
  zipcode: string,
  country: string
): Promise<MedicinePriceResult[]> {
  const localCurrency = getLocalCurrency(country);

  try {
    return await lookupViaScrapeGraph(medicine, zipcode, country, localCurrency);
  } catch (err: any) {
    console.warn(`[PriceLookup] ScrapeGraph failed for ${medicine}: ${err.message}`);
  }

  try {
    return await lookupViaOpenAI(medicine, zipcode, country, localCurrency);
  } catch (err: any) {
    console.error(`[PriceLookup] OpenAI fallback also failed for ${medicine}: ${err.message}`);
    return [priceUnavailableResult(medicine, localCurrency)];
  }
}
