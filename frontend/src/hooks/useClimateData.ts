import useSWR from "swr";
import { apiUrl, swrFetcher } from "@/lib/api";
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

export function useScenarios() {
  return useSWR<Scenario[]>(apiUrl("/api/v1/scenarios"), swrFetcher, opts);
}

export function useFacilities() {
  return useSWR<Facility[]>(apiUrl("/api/v1/company/facilities"), swrFetcher, opts);
}

export function useTransitionAnalysis(scenario: string, pricingRegime: string = "global") {
  return useSWR<TransitionRiskAnalysis>(
    apiUrl(`/api/v1/transition-risk/analysis?scenario=${scenario}&pricing_regime=${pricingRegime}`),
    swrFetcher,
    opts,
  );
}

export function useTransitionSummary(scenario: string, pricingRegime: string = "global") {
  return useSWR<TransitionRiskSummary>(
    apiUrl(`/api/v1/transition-risk/summary?scenario=${scenario}&pricing_regime=${pricingRegime}`),
    swrFetcher,
    opts,
  );
}

export function useTransitionComparison(pricingRegime: string = "global") {
  return useSWR<ScenarioComparison>(
    apiUrl(`/api/v1/transition-risk/comparison?pricing_regime=${pricingRegime}`),
    swrFetcher,
    opts,
  );
}

export function usePhysicalRisk(useApiData: boolean = false) {
  return useSWR<PhysicalRiskAssessment>(
    apiUrl(`/api/v1/physical-risk/assessment?use_api_data=${useApiData}`),
    swrFetcher,
    opts,
  );
}

export function useESGAssessment(framework: string) {
  return useSWR<ESGAssessment>(
    apiUrl(`/api/v1/esg/assessment?framework=${framework}`),
    swrFetcher,
    opts,
  );
}

export function useESGDisclosure(framework: string) {
  return useSWR<ESGDisclosureData>(
    apiUrl(`/api/v1/esg/disclosure-data?framework=${framework}`),
    swrFetcher,
    opts,
  );
}

export function useESGFrameworks() {
  return useSWR<ESGFramework[]>(apiUrl("/api/v1/esg/frameworks"), swrFetcher, opts);
}
