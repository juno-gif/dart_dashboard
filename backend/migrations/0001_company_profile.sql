-- 기업 개요(설립일/대표이사/주소/홈페이지/임직원수) 캐싱을 위한 컬럼 추가
-- Supabase SQL Editor에서 1회 실행하세요.

ALTER TABLE companies ADD COLUMN IF NOT EXISTS est_dt text;
ALTER TABLE companies ADD COLUMN IF NOT EXISTS ceo_nm text;
ALTER TABLE companies ADD COLUMN IF NOT EXISTS adres text;
ALTER TABLE companies ADD COLUMN IF NOT EXISTS hm_url text;
ALTER TABLE companies ADD COLUMN IF NOT EXISTS bizr_no text;
ALTER TABLE companies ADD COLUMN IF NOT EXISTS employee_count integer;
ALTER TABLE companies ADD COLUMN IF NOT EXISTS employee_count_source text;
ALTER TABLE companies ADD COLUMN IF NOT EXISTS profile_synced_at timestamptz;
