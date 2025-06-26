import { type NextRequest, NextResponse } from "next/server"

export async function POST(request: NextRequest) {
  try {
    const verificationData = await request.json()

    // Mock saving verification data
    const verification = {
      id: Math.floor(Math.random() * 1000) + 1,
      ...verificationData,
      verified_at: new Date().toISOString(),
    }

    return NextResponse.json({ verification })
  } catch (error) {
    return NextResponse.json({ error: "Server error" }, { status: 500 })
  }
}
