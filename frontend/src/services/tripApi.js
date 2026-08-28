/**
 * Spotter TMS - Trip & HOS Planning API Service
 */

export const ApiErrorType = {
  ROUTE_ERROR: 'ROUTE_ERROR',
  HOS_ERROR: 'HOS_ERROR',
  HOS_VIOLATION: 'HOS_VIOLATION',
  SERVER_ERROR: 'SERVER_ERROR',
  NETWORK_ERROR: 'NETWORK_ERROR',
};

export async function planTripApi(params) {
  try {
    const response = await fetch('/api/trips/plan/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        current_location: params.current_location,
        pickup_location: params.pickup_location,
        dropoff_location: params.dropoff_location,
        cycle_used_hours: Number(params.cycle_used_hours) || 0.0,
        start_time: params.start_time || undefined,
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      const errorMsg = data.error || 'Failed to plan trip';
      let errorType = ApiErrorType.SERVER_ERROR;

      if (response.status === 400) {
        if (errorMsg.toLowerCase().includes('geocode') || errorMsg.toLowerCase().includes('location')) {
          errorType = ApiErrorType.ROUTE_ERROR;
        } else if (errorMsg.toLowerCase().includes('cycle') || errorMsg.toLowerCase().includes('hos')) {
          errorType = ApiErrorType.HOS_ERROR;
        }
      } else if (response.status === 502) {
        errorType = ApiErrorType.ROUTE_ERROR;
      }

      const err = new Error(errorMsg);
      err.type = errorType;
      err.details = data.details;
      throw err;
    }

    // Check if the backend returned an HOS violation
    if (data.validation && !data.validation.is_valid) {
      data.hasViolations = true;
    }

    return data;
  } catch (err) {
    if (!err.type) {
      err.type = ApiErrorType.NETWORK_ERROR;
    }
    throw err;
  }
}
