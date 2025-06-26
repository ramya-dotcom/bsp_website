import { type NextRequest, NextResponse } from "next/server"

// Mock password verification (in real app, use bcrypt)
const verifyPassword = (password: string, hash: string) => {
  return password === "password123" // Simplified for demo
}

export async function POST(request: NextRequest) {
  try {
    const { email, password } = await request.json()

    // Mock database query
    const mockUsers = [
      { id: 1, email: "admin@example.com", password_hash: "hashed", is_admin: true, created_at: "2024-01-01" },
      { id: 2, email: "user@example.com", password_hash: "hashed", is_admin: false, created_at: "2024-01-01" },
      { id: 3, email: "john.doe@example.com", password_hash: "hashed", is_admin: false, created_at: "2024-01-01" },
    ]

    const user = mockUsers.find((u) => u.email === email)

    if (!user || !verifyPassword(password, user.password_hash)) {
      return NextResponse.json({ error: "Invalid credentials" }, { status: 401 })
    }

    const { password_hash, ...userWithoutPassword } = user
    return NextResponse.json({ user: userWithoutPassword })
  } catch (error) {
    return NextResponse.json({ error: "Server error" }, { status: 500 })
  }
}
