"""Trip Planning API Views."""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from .serializers import PlanTripRequestSerializer
from .services import trip_planner


@method_decorator(csrf_exempt, name="dispatch")
class PlanTripView(APIView):
    """POST /api/trips/plan/

    Accepts trip locations and cycle hours, performs geocoding, OSRM routing,
    and HOS scheduling, returning a validated multi-day driver schedule.
    """

    def post(self, request, *args, **kwargs):
        serializer = PlanTripRequestSerializer(data=request.data)
        if not serializer.is_valid():
            # Extract first readable error message for direct UI display
            first_err = "Invalid trip input."
            for field_name, err_list in serializer.errors.items():
                if isinstance(err_list, list) and len(err_list) > 0:
                    first_err = str(err_list[0])
                    break
                elif isinstance(err_list, str):
                    first_err = err_list
                    break

            return Response(
                {"error": first_err, "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        validated_data = serializer.validated_data

        try:
            result = trip_planner.plan_trip(
                current_location=validated_data["current_location"],
                pickup_location=validated_data["pickup_location"],
                dropoff_location=validated_data["dropoff_location"],
                cycle_used_hours=validated_data.get("cycle_used_hours", 0.0),
                start_time=validated_data.get("start_time"),
            )
            return Response(result, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"error": f"Trip Planning Error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
