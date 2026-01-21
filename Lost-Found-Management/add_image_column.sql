-- Run this SQL script to add image_path column to existing database
-- This is only needed if your database already exists

-- Check if column exists before adding
DO $$ 
BEGIN 
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'item' 
        AND column_name = 'image_path'
    ) THEN
        ALTER TABLE item ADD COLUMN image_path VARCHAR(255);
        RAISE NOTICE 'Column image_path added successfully';
    ELSE
        RAISE NOTICE 'Column image_path already exists';
    END IF;
END $$;

-- Optional: Create index for better performance
CREATE INDEX IF NOT EXISTS idx_item_image_path ON item(image_path);