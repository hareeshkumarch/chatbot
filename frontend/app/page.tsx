import { LandingNav } from "@/components/landing/LandingNav";
import { Hero } from "@/components/landing/Hero";
import { CapabilitiesSection } from "@/components/landing/CapabilitiesSection";
import { RoutingExplainerSection } from "@/components/landing/RoutingExplainerSection";
import { ArchitectureSection } from "@/components/landing/ArchitectureSection";
import { ReportsSection } from "@/components/landing/ReportsSection";
import { TrustSection } from "@/components/landing/TrustSection";
import { ClosingCta, LandingFooter } from "@/components/landing/ClosingCta";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-canvas">
      <LandingNav />
      <Hero />
      <CapabilitiesSection />
      <RoutingExplainerSection />
      <ArchitectureSection />
      <ReportsSection />
      <TrustSection />
      <ClosingCta />
      <LandingFooter />
    </div>
  );
}
