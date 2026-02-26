"use client";
import { useState, useEffect } from "react";

export function usePartner() {
    const [partnerId, setPartnerId] = useState<string | null>(null);
    const [companyName, setCompanyName] = useState<string | null>(null);

    useEffect(() => {
        const storedId = localStorage.getItem("cr_partner_id");
        const storedName = localStorage.getItem("cr_partner_name");

        setPartnerId(storedId);
        setCompanyName(storedName);

        const handleUpdate = () => {
            setPartnerId(localStorage.getItem("cr_partner_id"));
            setCompanyName(localStorage.getItem("cr_partner_name"));
        };

        window.addEventListener("partner_changed", handleUpdate);
        return () => window.removeEventListener("partner_changed", handleUpdate);
    }, []);

    const setPartner = (id: string | null, name: string | null = null) => {
        if (id) {
            localStorage.setItem("cr_partner_id", id);
            if (name) localStorage.setItem("cr_partner_name", name);
        } else {
            localStorage.removeItem("cr_partner_id");
            localStorage.removeItem("cr_partner_name");
        }
        window.dispatchEvent(new Event("partner_changed"));
    };

    return { partnerId, companyName, setPartner };
}
