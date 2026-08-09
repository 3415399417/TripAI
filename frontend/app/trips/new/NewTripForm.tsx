"use client";

import { useSearchParams } from "next/navigation";
import TripForm from "@/components/TripForm";

export default function NewTripForm() {
  const params = useSearchParams();
  const destination = params.get("destination") ?? "";
  const interestsRaw = params.get("interests") ?? "";
  const interests = interestsRaw
    ? interestsRaw.split(",").filter(Boolean)
    : [];

  return <TripForm initialDestination={destination} initialInterests={interests} />;
}
