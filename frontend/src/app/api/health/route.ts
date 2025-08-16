import { NextResponse } from 'next/server';

export async function GET() {
  try {
    // Простая проверка здоровья frontend
    const healthData = {
      status: 'healthy',
      timestamp: new Date().toISOString(),
      service: 'graphrag-frontend',
      version: process.env.NEXT_PUBLIC_APP_VERSION || '1.0.0',
      uptime: process.uptime(),
    };

    return NextResponse.json(healthData, { status: 200 });
  } catch (error) {
    return NextResponse.json(
      {
        status: 'unhealthy',
        timestamp: new Date().toISOString(),
        error: error instanceof Error ? error.message : 'Unknown error',
      },
      { status: 503 }
    );
  }
}
