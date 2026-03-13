import Anthropic from "@anthropic-ai/sdk";

const client = new Anthropic({
  apiKey: process.env.ANTHROPIC_API_KEY,
});

export async function generateDoctorNote(
  clinicalSummary: string,
  relayTranscript: Array<{ speaker: string; textOriginal: string; textTranslated: string }>,
  patientName: string,
  patientLanguage: string
): Promise<{
  diagnosis: string;
  prescribedMedications: string[];
  instructions: string;
  followUp: string;
  fullNoteText: string;
}> {
  const transcriptText =
    relayTranscript.length > 0
      ? relayTranscript
          .map(
            (m) =>
              `[${m.speaker.toUpperCase()}] ${m.textTranslated || m.textOriginal}`
          )
          .join("\n")
      : "No doctor-patient consultation transcript available yet.";

  const msg = await client.messages.create({
    model: "claude-haiku-4-5-20251001",
    max_tokens: 1000,
    messages: [
      {
        role: "user",
        content: `You are a medical AI assistant helping generate a doctor note. Based on the following patient intake data and doctor-patient consultation transcript, generate a structured doctor note.

PATIENT: ${patientName} (Language: ${patientLanguage})

INTAKE SUMMARY:
${clinicalSummary}

CONSULTATION TRANSCRIPT:
${transcriptText}

Generate the note in this exact JSON format (no markdown, just raw JSON):
{
  "diagnosis": "Primary diagnosis based on symptoms and consultation",
  "prescribedMedications": ["Medication 1 with dosage", "Medication 2 with dosage"],
  "instructions": "Patient care instructions",
  "followUp": "Follow-up recommendations",
  "fullNoteText": "The complete formatted doctor note as plain text"
}

Be professional and concise. Use clinical language appropriate for a medical record.`,
      },
    ],
  });

  const text = msg.content[0].type === "text" ? msg.content[0].text : "";

  try {
    return JSON.parse(text);
  } catch {
    // If Claude didn't return valid JSON, wrap the text
    return {
      diagnosis: "",
      prescribedMedications: [],
      instructions: "",
      followUp: "",
      fullNoteText: text,
    };
  }
}
