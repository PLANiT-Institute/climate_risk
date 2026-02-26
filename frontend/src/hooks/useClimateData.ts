import useSWR from "swr";
import { apiUrl, swrFetcher } from "@/lib/api";
import { usePartner } from "./usePartner";
import type {
  Scenario,
  Facility,
  TransitionRiskAnalysis,
  TransitionRiskSummary,
  ScenarioComparison,
  PhysicalRiskAssessment,
  ESGAssessment,
  ESGDisclosureData,
  ESGFramework,
} from "@/lib/api";

const opts = { revalidateOnFocus: false };

function buildUrl(basePath: string, partnerId: string | null) {
  if (partnerId) {
    return apiUrl(`/api/v1/partner/sessions/${partnerId}${basePath}`);
  }
  return apiUrl(`/api/v1${basePath}`);
}

export function useScenarios() {
  return useSWR<Scenario[]>(apiUrl("/api/v1/scenarios"), swrFetcher, opts);
}

export function useESGFrameworks() {
  return useSWR<ESGFramework[]>(apiUrl("/api/v1/esg/frameworks"), swrFetcher, opts);
}

export function useFacilities() {
  const { partnerId } = usePartner();
  // Partner root for facilities is different: /api/v1/partner/sessions/{pid}/facilities
  return useSWR<Facility[]>(
    buildUrl(partnerId ? "/facilities" : "/company/facilities", partnerId),
    swrFetcher,
    opts
  );
}

export function useTransitionAnalysis(scenario: string, pricingRegime: string = "global") {
  const { partnerId } = usePartner();
  return useSWR<TransitionRiskAnalysis>(
    buildUrl(`/transition-risk/analysis?scenario=${scenario}&pricing_regime=${pricingRegime}`, partnerId),
    swrFetcher,
    opts,
  );
}

export function useTransitionSummary(scenario: string, pricingRegime: string = "global") {
  const { partnerId } = usePartner();
  return useSWR<TransitionRiskSummary>(
    buildUrl(`/transition-risk/summary?scenario=${scenario}&pricing_regime=${pricingRegime}`, partnerId),
    swrFetcher,
    opts,
  );
}

export function useTransitionComparison(pricingRegime: string = "global") {
  const { partnerId } = usePartner();
  return useSWR<ScenarioComparison>(
    buildUrl(`/transition-risk/comparison?pricing_regime=${pricingRegime}`, partnerId),
    swrFetcher,
    opts,
  );
}

export function usePhysicalRisk(useApiData: boolean = false) {
  const { partnerId } = usePartner();
  return useSWR<PhysicalRiskAssessment>(
    buildUrl(`/physical-risk/assessment?use_api_data=${useApiData}`, partnerId),
    swrFetcher,
    opts,
  );
}

export function useESGAssessment(framework: string) {
  const { partnerId } = usePartner();
  return useSWR<ESGAssessment>(
    buildUrl(`/esg/assessment?framework=${framework}`, partnerId),
    swrFetcher,
    opts,
  );
}

export function useESGDisclosure(framework: string) {
  const { partnerId } = usePartner();
  return useSWR<ESGDisclosureData>(
    buildUrl(`/esg/disclosure-data?framework=${framework}`, partnerId),
    swrFetcher,
    opts,
  );
}
