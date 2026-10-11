-- Run once in your Supabase project's SQL Editor.
create table if not exists public.applications (
    id uuid primary key,
    user_id uuid not null references auth.users(id) on delete cascade,
    company text not null check (char_length(trim(company)) between 1 and 120),
    role text not null check (char_length(trim(role)) between 1 and 120),
    applied_date date not null,
    status text not null check (status in ('Applied','Online Assessment','Interview','Offer','Rejected','Withdrawn')),
    created_at timestamptz not null default now()
);
create index if not exists applications_user_id_idx on public.applications(user_id);
alter table public.applications enable row level security;

-- Only the signed-in owner can access their rows.
create policy "Owners can select applications" on public.applications
    for select to authenticated using ((select auth.uid()) = user_id);
create policy "Owners can insert applications" on public.applications
    for insert to authenticated with check ((select auth.uid()) = user_id);
create policy "Owners can update applications" on public.applications
    for update to authenticated using ((select auth.uid()) = user_id)
    with check ((select auth.uid()) = user_id);
create policy "Owners can delete applications" on public.applications
    for delete to authenticated using ((select auth.uid()) = user_id);
