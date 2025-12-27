export interface Lead {
    id: string;
    address_street: string;
    address_zip: string;
    status: string;
    distress_score: number;
    owner_name?: string;
}
