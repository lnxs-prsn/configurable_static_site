/**
 * Tusmo ry — Contact Form Handler
 * Netlify Functions implementation
 *
 * HTTP Contract:
 *   POST  application/x-www-form-urlencoded
 *   Fields: name, email, message
 *   200 = success (no body)
 *   400 = validation failed (no body)
 *   500 = email send failed (no body)
 */

exports.handler = async (event) => {
  // CORS headers for all responses
  const corsHeaders = {
    "Access-Control-Allow-Origin": "*",
  };

  // CORS preflight
  if (event.httpMethod === "OPTIONS") {
    return {
      statusCode: 204,
      headers: {
        ...corsHeaders,
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
      },
      body: "",
    };
  }

  // Only accept POST
  if (event.httpMethod !== "POST") {
    return {
      statusCode: 405,
      headers: corsHeaders,
      body: "",
    };
  }

  // Parse form data from query string format
  const params = new URLSearchParams(event.body);
  const name = (params.get("name") || "").trim();
  const email = (params.get("email") || "").trim();
  const message = (params.get("message") || "").trim();

  // Validation: all fields non-empty, email contains @
  if (!name || !email || !message || !email.includes("@")) {
    return {
      statusCode: 400,
      headers: corsHeaders,
      body: "",
    };
  }

  // Call Resend API
  const resendApiKey = process.env.RESEND_API_KEY;
  if (!resendApiKey) {
    return {
      statusCode: 500,
      headers: corsHeaders,
      body: "",
    };
  }

  try {
    const response = await fetch("https://api.resend.com/emails", {
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

    if (!response.ok) {
      return {
        statusCode: 500,
        headers: corsHeaders,
        body: "",
      };
    }

    return {
      statusCode: 200,
      headers: corsHeaders,
      body: "",
    };
  } catch {
    return {
      statusCode: 500,
      headers: corsHeaders,
      body: "",
    };
  }
};
