import { type NextRequest, NextResponse } from "next/server"

export async function POST(request: NextRequest) {
  try {
    const { email, password } = await request.json()

    // Mock user creation (in real app, hash password and save to database)
    const newUser = {
      id: Math.floor(Math.random() * 1000) + 100,
      email,
      is_admin: false,
      created_at: new Date().toISOString(),
    }

    return NextResponse.json({ user: newUser })
  } catch (error) {
    return NextResponse.json({ error: "Server error" }, { status: 500 })
  }
}
