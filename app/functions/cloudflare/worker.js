/**
 * Tusmo ry — Contact Form Handler
 * Cloudflare Workers implementation
 *
 * HTTP Contract:
 *   POST  application/x-www-form-urlencoded
 *   Fields: name, email, message
 *   200 = success (no body)
 *   400 = validation failed (no body)
 *   500 = email send failed (no body)
 */

export default {
  async fetch(request, env) {
    // CORS preflight
    if (request.method === "OPTIONS") {
      return new Response(null, {
        status: 204,
        headers: {
          "Access-Control-Allow-Origin": "*",
          "Access-Control-Allow-Methods": "POST, OPTIONS",
          "Access-Control-Allow-Headers": "Content-Type",
        },
      });
    }

    // Only accept POST
    if (request.method !== "POST") {
      return new Response(null, {
        status: 405,
        headers: { "Access-Control-Allow-Origin": "*" },
      });
    }

    // Parse form data
    let formData;
    try {
      formData = await request.formData();
    } catch {
      return new Response(null, {
        status: 400,
        headers: { "Access-Control-Allow-Origin": "*" },
      });
    }

    const name = (formData.get("name") || "").toString().trim();
    const email = (formData.get("email") || "").toString().trim();
    const message = (formData.get("message") || "").toString().trim();

    // Validation: all fields non-empty, email contains @
    if (!name || !email || !message || !email.includes("@")) {
      return new Response(null, {
        status: 400,
        headers: { "Access-Control-Allow-Origin": "*" },
      });
    }

    // Call Resend API
    const resendApiKey = env.RESEND_API_KEY;
    if (!resendApiKey) {
      return new Response(null, {
        status: 500,
        headers: { "Access-Control-Allow-Origin": "*" },
      });
    }

    try {
      const resendResponse = await fetch("https://api.resend.com/emails", {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${resendApiKey}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          from: "Tusmo ry <onboarding@resend.dev>",
          to: "Tusmo.ry@hotmail.com",
          reply_to: "Tusmo.ry@hotmail.com",
          subject: `Yhteydenotto: ${name}`,
          text: `Nimi: ${name}\nSähköposti: ${email}\n\nViesti:\n${message}`,
        }),
      });

      if (!resendResponse.ok) {
        return new Response(null, {
          status: 500,
          headers: { "Access-Control-Allow-Origin": "*" },
        });
      }

      return new Response(null, {
        status: 200,
        headers: { "Access-Control-Allow-Origin": "*" },
      });
    } catch {
      return new Response(null, {
        status: 500,
        headers: { "Access-Control-Allow-Origin": "*" },
      });
    }
  },
};
