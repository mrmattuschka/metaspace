import { Entity, PrimaryColumn, Column, Index } from 'typeorm';
import { Moment } from 'moment';
import { MomentValueTransformer } from '../../utils/MomentValueTransformer';

type DiagnosticType = 'TIC' | 'AUTO_PREVIEW' | 'MOST_ABUNDANT_PEAK'
export const DiagnosticTypeOptions = {
  TIC: 'TIC',
  AUTO_PREVIEW: 'AUTO_PREVIEW',
}

@Entity()
// NULL values can't conflict with other NULL values in unique indexes, so this
// unique index is split based on whether jobId is NULL or non-NULL
@Index(['datasetId','type','jobId'], {unique: true, where: 'jobId IS NOT NULL'})
@Index(['datasetId','type'], {unique: true, where: 'jobId IS NULL'})
export class DatasetDiagnostic {

  @PrimaryColumn({ type: 'uuid', default: () => 'uuid_generate_v1mc()' })
  id: string;

  @Column({ type: 'text', enum: Object.values(DiagnosticTypeOptions) })
  type: DiagnosticType;

  @Column({ name: 'ds_id', type: 'text' })
  datasetId: string;

  @Column({ type: 'text', nullable: true })
  jobId: string | null;

  @Column({ type: 'timestamp without time zone', default: () => "(now() at time zone 'utc')",
    transformer: new MomentValueTransformer() })
  updatedDT: Moment;

  @Column({ type: 'json', nullable: true })
  data: any;

  @Column({ type: 'text', nullable: true })
  error: any;

  @Column({ type: 'text', array: true })
  images: string[];
}

export const DIAGNOSTIC_ENTITIES = [
  DatasetDiagnostic,
];
