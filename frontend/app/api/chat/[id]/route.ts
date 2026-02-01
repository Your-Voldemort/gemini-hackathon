import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  try {
    const id = (await params).id;
    const apiUrl = `http://localhost:8000/api/chat/session/${id}`;

    const response = await fetch(apiUrl);
    const data = await response.json();

    if (!response.ok || data?.success === false) {
      return NextResponse.json(
        { error: data?.detail || data?.error || 'Failed to fetch session' },
        { status: response.status || 500 }
      );
    }

    return NextResponse.json(data);
  } catch (error) {
    console.error('Error fetching thinking logs:', error);
    return NextResponse.json({ error: 'Failed to fetch thinking logs' }, { status: 500 });
  }
}
