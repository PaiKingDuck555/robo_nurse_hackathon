"use client";

import useSWR from "swr";

const fetcher = (url: string) => fetch(url).then((res) => res.json());

export function usePatientData() {
  const { data, error, isLoading, mutate } = useSWR("/api/patients?latest=true", fetcher, {
    refreshInterval: 3000,
  });

  return {
    patient: data?.patient || null,
    intakeSession: data?.intakeSession || null,
    relaySession: data?.relaySession || null,
    prescription: data?.prescription || null,
    isLoading,
    isError: error,
    mutate,
  };
}
