/**
 * Types for sharing resources between users.
 */

export interface ShareByEmailRequest {
  email: string;
}

export interface ShareResultResponse {
  status: 'shared' | 'pending';
  email: string;
  permission_level: string;
  share_id?: string;
  invite_id?: string;
  user_id?: string;
  granted_at?: string;
  created_at?: string;
}

export interface ActiveShareItem {
  share_id: string;
  user_id: string;
  email: string;
  display_name?: string | null;
  profile_picture_url?: string | null;
  permission_level: string;
  granted_at: string;
  status: 'active';
}

export interface PendingInviteItem {
  invite_id: string;
  email: string;
  permission_level: string;
  created_at: string;
  status: 'pending';
}

export interface ShareListResponse {
  resource_id: string;
  shares: ActiveShareItem[];
  pending: PendingInviteItem[];
}
