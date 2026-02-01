import { NextResponse } from 'next/server';

export async function GET() {
  try {
    const response = await fetch('http://localhost:8000/api/contracts');
    const data = await response.json();

    if (!response.ok || data?.success === false) {
      return NextResponse.json(
        {
          status: 'error',
          contracts: null,
          error: data?.error || data?.detail || 'Failed to fetch contracts',
        },
        { status: response.status || 500 }
      );
    }

    return NextResponse.json({
      status: 'success',
      contracts: data.contracts || [],
      count: data.count || 0,
      error: null,
    });
  } catch (error) {
    return NextResponse.json(
      {
        status: 'error',
        contracts: null,
        error: error instanceof Error ? error.message : 'An error occurred',
      },
      { status: 500 }
    );
  }
}

export async function POST(request: Request) {
  try {
    const formData = await request.formData();
    const file = formData.get('file');
    const name = formData.get('name');

    if (!file || !name) {
      return NextResponse.json(
        {
          status: 'error',
          error: 'File and name are required',
        },
        { status: 400 }
      );
    }

    const forwardForm = new FormData();
    const typedFile = file as File;
    forwardForm.append('file', typedFile, typedFile.name);
    forwardForm.append('name', String(name));

    const contractType = formData.get('contract_type');
    const parties = formData.get('parties');
    const notes = formData.get('notes');

    if (contractType) {
      forwardForm.append('contract_type', String(contractType));
    }
    if (parties) {
      forwardForm.append('parties', String(parties));
    }
    if (notes) {
      forwardForm.append('notes', String(notes));
    }

    const response = await fetch('http://localhost:8000/api/contracts/upload', {
      method: 'POST',
      body: forwardForm,
    });

    const data = await response.json();

    if (!response.ok || data?.success === false) {
      return NextResponse.json(
        {
          status: 'error',
          error: data?.detail || data?.error || 'Failed to upload contract',
        },
        { status: response.status || 500 }
      );
    }

    return NextResponse.json({
      status: 'success',
      contract_id: data.contract_id || null,
      message: data.message || 'Contract uploaded',
      error: null,
    });
  } catch (error) {
    return NextResponse.json(
      {
        status: 'error',
        error: error instanceof Error ? error.message : 'An error occurred',
      },
      { status: 500 }
    );
  }
}
